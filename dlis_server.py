from enum import Enum
import json
from typing import Sequence
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp.shared.exceptions import McpError
from dlisio import dlis
from pydantic import BaseModel


class DLISTools(str, Enum):
    ANALYZE_FILE = "analyze_file"
    GET_FILE_STRUCTURE = "get_file_structure"
    GET_SUMMARY = "get_summary"


class ChannelInfo(BaseModel):
    name: str
    unit: str


class FrameInfo(BaseModel):
    name: str
    channel_count: int
    channels: list[ChannelInfo]


class LogicalFileInfo(BaseModel):
    name: str
    parameters: dict | None = None
    frames: list[FrameInfo]


class FileStructure(BaseModel):
    number_of_logical_files: int
    logical_files: list[LogicalFileInfo]


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
    
    def get_file_structure(self) -> FileStructure:
        """Get the hierarchical structure of the DLIS file"""
        if not self.physical_file:
            self.load_file()
            
        structure = FileStructure(
            number_of_logical_files=len(list(self.physical_file)),
            logical_files=[]
        )
        
        for logical_file in self.physical_file:
            logical_file_info = LogicalFileInfo(
                name=str(logical_file.description),
                frames=[]
            )
            
            # Add origins information if available
            origins = logical_file.origins
            if origins and len(origins) > 0:
                origin = origins[0]
                logical_file_info.parameters = {
                    "origin": str(origin.origin),
                    "file_set": str(origin.file_set),
                    "file_number": str(origin.file_number),
                    "file_type": str(origin.file_type),
                    "product": str(origin.product),
                    "version": str(origin.version)
                }
            
            # Add frame information
            for frame in logical_file.frames:
                frame_info = FrameInfo(
                    name=str(frame.name),
                    channel_count=len(frame.channels),
                    channels=[]
                )
                
                # Add channel information
                for channel in frame.channels:
                    channel_info = ChannelInfo(
                        name=str(channel.name),
                        unit=str(channel.units)
                    )
                    frame_info.channels.append(channel_info)
                
                logical_file_info.frames.append(frame_info)
            
            structure.logical_files.append(logical_file_info)
        
        return structure
    
    def get_file_summary(self) -> str:
        """Generate a bullet-point summary of the file structure"""
        structure = self.get_file_structure()
        summary = []
        
        # Physical file level
        summary.append("Physical File")
        summary.append(f"  • Number of Logical Files: {structure.number_of_logical_files}")
        
        # Logical files level
        for lf in structure.logical_files:
            summary.append(f"\n  • Logical File: {lf.name}")
            if lf.parameters:
                params = lf.parameters
                summary.append(f"    - Origin: {params.get('origin', 'N/A')}")
                summary.append(f"    - File Set: {params.get('file_set', 'N/A')}")
                summary.append(f"    - File Number: {params.get('file_number', 'N/A')}")
                summary.append(f"    - File Type: {params.get('file_type', 'N/A')}")
                summary.append(f"    - Product: {params.get('product', 'N/A')}")
                summary.append(f"    - Version: {params.get('version', 'N/A')}")
            
            # Frames level
            for frame in lf.frames:
                summary.append(f"\n    • Frame: {frame.name}")
                summary.append(f"      - Number of Channels: {frame.channel_count}")
                
                # Channels level
                for channel in frame.channels:
                    summary.append(f"\n      • Channel: {channel.name}")
                    summary.append(f"        - Unit: {channel.unit}")
        
        return "\n".join(summary)


async def serve() -> None:
    server = Server("mcp-dlis")
    analyzer = None

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available DLIS analysis tools."""
        return [
            Tool(
                name=DLISTools.ANALYZE_FILE.value,
                description="Analyze a DLIS file and return basic information",
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
            Tool(
                name=DLISTools.GET_FILE_STRUCTURE.value,
                description="Get detailed structure of a DLIS file",
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
            Tool(
                name=DLISTools.GET_SUMMARY.value,
                description="Get a human-readable summary of a DLIS file structure",
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
                case DLISTools.ANALYZE_FILE.value:
                    analyzer.load_file()
                    with analyzer.physical_file as files:
                        logical_files_count = len(list(files))
                    
                    result = {
                        "success": True,
                        "file_path": file_path,
                        "logical_files_count": logical_files_count,
                        "message": f"Successfully analyzed DLIS file with {logical_files_count} logical file(s)"
                    }

                case DLISTools.GET_FILE_STRUCTURE.value:
                    structure = analyzer.get_file_structure()
                    result = {
                        "success": True,
                        "structure": structure.model_dump()
                    }

                case DLISTools.GET_SUMMARY.value:
                    summary = analyzer.get_file_summary()
                    result = {
                        "success": True,
                        "summary": summary
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