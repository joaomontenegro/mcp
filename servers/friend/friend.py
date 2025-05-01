#!/usr/bin/env python

from mcp.server.fastmcp import FastMCP
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import logging
import argparse
import subprocess
import sys

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('mcp-server')

# Define server metadata
server_name = "FriendInfoServer"
server_version = "1.0.0"
server_description = """
This server provides information about a friend.

This friend enjoys hiking, reading science fiction, 
and playing chess. He has been a close friend for over 20 years and is known
for his excellent cooking skills and dry sense of humor.

You can use this server to retrieve basic information about the friend, such as
name and age. In the future, more details and capabilities may be added.
"""

# Create an MCP server with metadata
mcp = FastMCP(
    name=server_name,
    version=server_version,
    description=server_description
)

# Add static resources for context
@mcp.resource("about://friend")
def friend_info() -> str:
    """Information about the friend"""
    return """
    This friend is an individual with a rich and interesting background.
    Born in Barcelona, he moved to the United States in his twenties to pursue
    a career in culinary arts. After working in several renowned restaurants,
    he opened his own tapas bar which became very successful.
    """

@mcp.resource("about://server")
def server_info() -> str:
    """Information about this MCP server"""
    return """
    This MCP (Model Context Protocol) server provides information about a friend.
    It's a simple demonstration of how MCP servers can provide contextual 
    information and tools to LLMs (Large Language Models).
    
    Current capabilities include:
    - Retrieving the friend's name
    - Retrieving the friend's age
    - Providing background information about the friend
    
    This server can be used by any MCP-compatible client, including Claude Desktop,
    Cursor AI, and other tools that support the Model Context Protocol. The
    information provided by this server helps the LLM give more accurate and
    contextually relevant responses when discussing the friend.
    """

# Define tools using the FastMCP decorators
@mcp.tool()
def get_name() -> dict:
    """Returns the name of your friend."""
    logger.info("get_name tool called")
    return { "name": "Quim" }

@mcp.tool()
def get_age() -> dict:
    """Returns the age of your friend."""
    logger.info("get_age tool called")
    return { "age": "69" }

@mcp.tool()
def get_aa_background() -> dict:
    """Returns some information about your friend that is not his age nor his name."""
    logger.info("get_aa_extra_background tool called")
    return { 
        "hobby": "Your friend likes to play chess",
        "home town": "Barcelona",
        "favorite book": "Dune"
    }


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='MCP Server with stdio/SSE transport')
    parser.add_argument('--transport', '-transport', choices=['stdio', 'sse'], default='stdio',
                      help='Transport type: stdio or sse (default: stdio)')
    parser.add_argument('--port', '-port', type=int, default=3001,
                      help='Port for SSE server (default: 3001)')
    parser.add_argument('--mcpo', '-mcpo', action='store_true',
                      help='Launch mcpo proxy when running in SSE mode')
    parser.add_argument('--mcpo-port', type=int, default=3002,
                      help='Port for mcpo proxy (default: 3002)')
    args = parser.parse_args()
    
    if args.transport == 'stdio':
        logger.info("Starting MCP server in stdio mode")
        # Run the server in stdio mode
        mcp.run()
    else:
        # Create Starlette app with CORS middleware for SSE
        app = Starlette(
            routes=[
                # Mount the SSE app at the root
                Mount('/', app=mcp.sse_app()),
            ],
            middleware=[
                Middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
            ]
        )
        
        logger.info(f"Starting MCP server in SSE mode on port {args.port}")
        logger.info(f"SSE endpoint available at http://localhost:{args.port}/sse")
        
        # If --mcpo is set, launch mcpo in the background
        mcpo_process = None
        if args.mcpo:
            server_url = f"http://localhost:{args.port}/sse"
            mcpo_command = [
                "mcpo",
                "--port", str(args.mcpo_port),
                "--server-type", "sse",
                "--cors-allow-origins", "*",
                "--",
                server_url
            ]
            
            logger.info(f"Launching mcpo with command: {' '.join(mcpo_command)}")
            
            # Start mcpo in the background
            try:
                mcpo_process = subprocess.Popen(mcpo_command)
                logger.info(f"Started mcpo (PID: {mcpo_process.pid})")
                logger.info(f"mcpo is now available at http://localhost:{args.mcpo_port}")
            except Exception as e:
                logger.error(f"Failed to start mcpo: {e}")
        else:
            logger.info(f"Use 'mcpo --port {args.mcpo_port} --server-type sse -- http://localhost:{args.port}/sse' to connect")
        
        # Run the ASGI app
        try:
            uvicorn.run(app, host="0.0.0.0", port=args.port)
        finally:
            # If mcpo was started, terminate it when the server stops
            if mcpo_process is not None:
                try:
                    mcpo_process.terminate()
                    logger.info("Terminated mcpo process")
                except:
                    pass