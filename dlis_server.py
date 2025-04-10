from enum import Enum
import json
from typing import Sequence
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp.shared.exceptions import McpError
from dlisio import dlis
from pydantic import BaseModel
import dlisio


class DLISTools(str, Enum):
    GET_CHANNEL = "get_channel"
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

    def get_channel(self, filename: str, framename: str, channelname: str):
        """Get channel data and units from a specific logical file, frame, and channel"""
        if not self.physical_file:
            self.load_file()
            
        # Check if logical file exists
        logical_file_found = False
        for lf in self.physical_file:
            if lf.fileheader.attic['ID'].value[0].strip() == filename:
                logical_file_found = True
                # Check if frame exists
                frame_found = False
                for frame in lf.frames:
                    if frame.name.strip() == framename:
                        frame_found = True
                        # Check if channel exists
                        channel_found = False
                        for channel in frame.channels:
                            if channel.name.strip() == channelname:
                                channel_found = True
                                return {
                                    "curves": channel.curves().tolist(),
                                    "units": channel.units
                                }
                        if not channel_found:
                            raise McpError(f"Channel '{channelname}' not found in frame '{framename}'")
                if not frame_found:
                    raise McpError(f"Frame '{framename}' not found in logical file '{filename}'")
        if not logical_file_found:
            raise McpError(f"Logical file '{filename}' not found in the DLIS file")
        
        return None

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
                file_id = lf.fileheader.attic.get('ID')
                assert file_id and file_id.value, "Invalid file ID"
                summary.append(f'fileheader: {file_id.value[0].strip()}:\n')
            except (AssertionError, AttributeError, IndexError):
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
                        summary.append(f'\t\t{sub_attr.name}: \n')
                    except (AssertionError, AttributeError, TypeError):
                        continue
                        
                    for subsub_attr in subsub_attrs:
                        try:
                            # Get value and process it
                            value = sub_attr.attic.get(subsub_attr)
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

        return ''.join(summary)


async def serve() -> None:
    server = Server("mcp-dlis")
    analyzer = None

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available DLIS analysis tools."""
        return [
            Tool(
                name=DLISTools.GET_CHANNEL.value,
                description="Get channel data and units from a specific logical file, frame, and channel",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the DLIS file to analyze",
                        },
                        "filename": {
                            "type": "string",
                            "description": "Name of the logical file",
                        },
                        "framename": {
                            "type": "string",
                            "description": "Name of the frame",
                        },
                        "channelname": {
                            "type": "string",
                            "description": "Name of the channel",
                        }
                    },
                    "required": ["file_path", "filename", "framename", "channelname"],
                },
            ),
            Tool(
                name=DLISTools.GET_META.value,
                description="Get detailed metadata from the DLIS file with hierarchical structure",
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
                case DLISTools.GET_CHANNEL.value:
                    filename = arguments.get("filename")
                    framename = arguments.get("framename")
                    channelname = arguments.get("channelname")
                    
                    if not all([filename, framename, channelname]):
                        raise ValueError("Missing required arguments for get_channel")
                    
                    channel_data = analyzer.get_channel(filename, framename, channelname)
                    result = {
                        "success": True,
                        "channel_data": channel_data
                    }

                case DLISTools.GET_META.value:
                    meta = analyzer.get_meta()
                    result = {
                        "success": True,
                        "meta": meta
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