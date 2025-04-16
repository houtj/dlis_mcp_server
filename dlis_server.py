from enum import Enum
import json
from typing import Sequence
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp.shared.exceptions import McpError
from dlisio import dlis
import numpy as np
from pydantic import BaseModel
from pathlib import Path

class DLISTools(str, Enum):
    EXTRACT_CHANNELS = "extract_channels"
    GET_META = "get_meta"


class DLISAnalyzer:
    """Analyzer for DLIS files"""
    
    def __init__(self, file_path: str):
        """Initialize with path to DLIS file"""
        self.file_path = file_path
        self.physical_file = None
        
    def load_file(self) -> bool:
        """Load the DLIS file"""
        try:
            self.physical_file = dlis.load(self.file_path)
            return True
        except Exception as e:
            raise McpError(f"Error loading DLIS file: {str(e)}")
    
    def extract_channels(self):
        """Extract all channels from the DLIS file and save to folder structure"""
        if not self.physical_file:
            self.load_file()
            
        # Create base output folder at same level as input file
        input_path = Path(self.file_path)
        base_folder = input_path.parent / f'{input_path.stem}_channels'
        base_folder.mkdir(exist_ok=True)
        
        # Track used names to handle duplicates
        used_lf_names = set()
        
        for lf in self.physical_file:
            # Get logical file name and sanitize
            lf_name = lf.fileheader.attic['ID'].value[0].strip()
            lf_name = "".join(c if c not in '<>:"/\\|?*' else "_" for c in lf_name)
            
            # Handle duplicate names
            orig_lf_name = lf_name
            while lf_name in used_lf_names:
                lf_name = f"{orig_lf_name}_"
            used_lf_names.add(lf_name)
            
            # Create logical file folder
            lf_folder = base_folder / lf_name
            lf_folder.mkdir(exist_ok=True)
            
            # Reset used names for frames
            used_frame_names = set()
            
            for frame in lf.frames:
                # Get frame name and sanitize
                frame_name = frame.name.strip()
                frame_name = "".join(c if c not in '<>:"/\\|?*' else "_" for c in frame_name)
                
                # Handle duplicate names
                orig_frame_name = frame_name
                while frame_name in used_frame_names:
                    frame_name = f"{orig_frame_name}_"
                used_frame_names.add(frame_name)
                
                # Create frame folder
                frame_folder = lf_folder / frame_name
                frame_folder.mkdir(exist_ok=True)
                
                # Reset used names for channels
                used_channel_names = set()
                
                for channel in frame.channels:
                    # Get channel name and sanitize
                    channel_name = channel.name.strip()
                    channel_name = "".join(c if c not in '<>:"/\\|?*' else "_" for c in channel_name)
                    
                    # Handle duplicate names
                    orig_channel_name = channel_name
                    while channel_name in used_channel_names:
                        channel_name = f"{orig_channel_name}_"
                    used_channel_names.add(channel_name)
                    
                    try:
                        # Create channel folder
                        channel_folder = frame_folder / channel_name
                        channel_folder.mkdir(exist_ok=True)
                        
                        # Save channel data to NPY file
                        curves = channel.curves()
                        npy_path = channel_folder / "values.npy"
                        np.save(npy_path, curves)
                        
                        # Save channel metadata to JSON
                        meta_path = channel_folder / "meta.json"
                        with open(meta_path, 'w') as f:
                            json.dump({"unit": channel.units}, f)
                            
                    except Exception as e:
                        print(f"Error saving channel {channel_name}: {str(e)}")
                        continue
        return str(base_folder)

    def get_meta(self):
        """Extract metadata from the DLIS file with hierarchical structure"""
        if not self.physical_file:
            self.load_file()

        meta_attr_list = [
            'axes', 'calibrations', 'channels', 'coefficients', 'comments',
            'computations', 'equipments', 'frames', 'groups', 'longnames',
            'measurements', 'messages', 'origins', 'parameters', 'paths',
            'processes', 'splices', 'tools', 'wellrefs', 'zones'
        ]
        
        summary = []
        for lf in self.physical_file:
            try:
                # Get file header
                file_id = lf.fileheader.attic['ID']
                assert file_id and file_id.value, "Invalid file ID"
                summary.append(f'fileheader: {file_id.value[0].strip()}:\n')
            except (AssertionError, AttributeError, IndexError, KeyError):
                continue
            
            for attr in meta_attr_list:
                try:
                    # Get attribute value
                    attr_value = getattr(lf, attr)
                    assert hasattr(attr_value, '__len__') and len(attr_value) > 0, "Invalid attribute value"
                    summary.append(f'\t{attr}: \n')
                except (AssertionError, AttributeError):
                    continue
                    
                for sub_attr in attr_value:
                    try:
                        # Get sub-attribute info
                        assert hasattr(sub_attr, 'attic') and hasattr(sub_attr, 'name'), "Invalid sub-attribute"
                        subsub_attrs = sub_attr.attic.keys()
                        if len(subsub_attrs)== 0: continue
                        summary.append(f'\t\t{sub_attr.name}: \n')
                    except (AssertionError, AttributeError, TypeError):
                        continue
                        
                    for subsub_attr in subsub_attrs:
                        try:
                            # Get value and process it
                            value = sub_attr.attic[subsub_attr]
                            assert value and hasattr(value, 'value'), "Invalid value"
                            
                            # Process value list
                            processed_value = []
                            for x in value.value:
                                try:
                                    processed_value.append(x.id if hasattr(x, 'id') else x)
                                except (AttributeError, TypeError):
                                    continue
                            
                            assert processed_value, "No valid values found"
                            value = processed_value[0] if len(processed_value) == 1 else processed_value
                            
                            # Get units
                            unit = getattr(value, 'units', '')
                            
                            # Format and append value
                            value_str = str(value)
                            assert value_str, "Empty value string"
                            value_str = value_str.replace('\r\n', ' ').replace('\n', ' ')
                            
                            summary.append(
                                f'\t\t\t{subsub_attr}({unit}): {value_str}\n' if unit 
                                else f'\t\t\t{subsub_attr}: {value_str}\n'
                            )
                                
                        except (AssertionError, AttributeError, TypeError, KeyError):
                            continue
        summary = ''.join(summary)
        # Write to meta.txt in same folder as input file
        input_path = Path(self.file_path)
        output_path = input_path.parent / f'{input_path.stem}_meta.txt'
        # Write summary to output file
        with open(output_path, 'w') as f:
            f.write(summary)
        return str(output_path)


async def serve() -> None:
    server = Server("mcp-dlis")
    analyzer = None

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available DLIS analysis tools."""
        return [
            Tool(
                name=DLISTools.EXTRACT_CHANNELS.value,
                description="Extract all channel data from a DLIS file, including values, units. Returns path to folder containing extracted channel data",
                inputSchema={
                    "type": "object", 
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the DLIS file to analyze"
                        }
                    },
                    "required": ["file_path"]
                }
            ),
            Tool(
                name=DLISTools.GET_META.value,
                description="Get detailed metadata from the DLIS file with hierarchical structure, including file headers, axes, channels, frames, measurements, and origins. Returns path to generated metadata text file.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the DLIS file to analyze",
                        }
                    },
                    "required": ["file_path"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> Sequence[TextContent]:
        """Handle tool calls for DLIS file analysis."""
        try:
            file_path = arguments.get("file_path")
            if not file_path:
                raise ValueError("Missing required argument: file_path")

            analyzer = DLISAnalyzer(file_path)
            
            match name:
                case DLISTools.EXTRACT_CHANNELS.value:
                    output_path = analyzer.extract_channels()
                    result = {
                        "success": True,
                        "output_path": output_path
                    }

                case DLISTools.GET_META.value:
                    output_path = analyzer.get_meta()
                    result = {
                        "success": True,
                        "output_path": output_path
                    }

                case _:
                    raise ValueError(f"Unknown tool: {name}")

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            raise McpError(f"Error processing DLIS analysis: {str(e)}")

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)


if __name__ == "__main__":
    import asyncio
    asyncio.run(serve()) 