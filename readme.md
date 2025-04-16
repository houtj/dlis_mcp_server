# DLIS MCP Server

A Model Context Protocol server that provides DLIS (Digital Log Interchange Standard) file analysis capabilities. This server enables LLMs to extract and analyze data from DLIS files, commonly used in the oil and gas industry for well logging data.

## Available Tools

### get_meta
Get metadata from a DLIS file with hierarchical structure.

Required arguments:
- file_path (path to the DLIS file)

### extract_channels
Extract all channels from the DLIS file and save to a folder structure.

Required arguments:
- file_path (path to the DLIS file)

## Installation

### Using uv (recommended)
When using uv no specific installation is needed. We will use uvx to directly run dlis-mcp-server.

### Using PIP
Alternatively you can install dlis-mcp-server via pip: