# DLIS MCP Server

A Model Context Protocol server that provides DLIS (Digital Log Interchange Standard) file analysis capabilities. This server enables LLMs to extract information from DLIS files, including channel data and metadata, with support for hierarchical data structures.

## Features

- Extract channel data from DLIS files
- Analyze DLIS file metadata
- Support for hierarchical data structures
- Easy integration with LLM applications

## Installation

### Using pip

```bash
pip install mcp_server_dlis
```

After installation, you can run it as a script using:

```bash
python -m mcp_server_dlis
```

## Configuration

### Configure for Claude.app

Add to your Claude settings:

```json
"mcpServers": {
  "dlis": {
    "command": "python",
    "args": ["-m", "mcp_server_time"]
  }
}
```

## Available Tools

- `extract_channels` - Extracts all channels from a DLIS file and saves them to a folder structure.
  - Required arguments:
    - `file_path`: Path to the DLIS file to analyze


- `get Metadata` - Extracts metadata from a DLIS file with hierarchical structure.
  - Required arguments:
    - `file_path`: Path to the DLIS file to analyze


## Example Usage

1. Extract channels from a DLIS file:
```json
{
  "name": "extract_channels",
  "arguments": {
    "file_path": "path/to/your/dlis_file.dlis"
  }
}
```
Response:
```json
{
  "output_path": "path/to/the/output/folder"
}
```

2. Get metadata from a DLIS file:
```json
{
  "name": "extract_channels",
  "arguments": {
    "file_path": "path/to/your/dlis_file.dlis"
  }
}
```
Response:
```json
{
  "output_path": "path/to/the/output/file.txt"
}
```

## Debugging

You can use the MCP inspector to debug the server:

```bash
npx @modelcontextprotocol/inspector mcp_server_dlis
```

## Examples of Questions for Claude

1. "What channels are available in this DLIS file at path/to/dlis/file.dlis?"
2. "Show me the metadata structure of this DLIS file at path/to/dlis/file.dlis"
3. "Extract all channels from this DLIS file at path/to/dlis/file.dlis"

## Contributing

We encourage contributions to help expand and improve mcp_server_dlis. Whether you want to add new DLIS analysis tools, enhance existing functionality, or improve documentation, your input is valuable.

For examples of other MCP servers and implementation patterns, see:
https://github.com/modelcontextprotocol/servers

Pull requests are welcome! Feel free to contribute new ideas, bug fixes, or enhancements to make mcp_server_dlis even more powerful and useful.

## License

mcp_server_dlis is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.