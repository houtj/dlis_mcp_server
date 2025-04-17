"""
DLIS MCP Server - A DLIS server implementation for MCP
"""

__version__ = "0.1.0" 

from .dlis_server import serve


def main():
    """MCP Time Server - Time and timezone conversion functionality for MCP"""
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        description="give a model the ability to handle time queries and timezone conversions"
    )
    asyncio.run(serve())


if __name__ == "__main__":
    main()