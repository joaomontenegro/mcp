#!/usr/bin/env python

from mcp.server.fastmcp import FastMCP
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import logging

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
    
    In his free time, he enjoys hiking in national parks, reading science fiction
    novels (particularly works by Ursula K. Le Guin and Isaac Asimov), and playing
    chess at a competitive level. He has participated in several regional chess
    tournaments and has achieved a respectable ELO rating.
    
    He is known among his friends for his excellent cooking skills, especially
    his paella and tortilla española, as well as his dry sense of humor. He's
    been a loyal friend for over two decades and is always willing to offer wise
    advice based on his diverse life experiences.
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
def get_name() -> str:
    """Returns the name of your friend."""
    logger.info("get_name tool called")
    return "Quim"

@mcp.tool()
def get_age() -> int:
    """Returns the current age of your friend as an integer."""
    logger.info("get_age tool called")
    return 69

# Create Starlette app with CORS middleware
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

if __name__ == "__main__":
    port = 5000
    logger.info(f"Starting MCP server on port {port}")
    logger.info(f"SSE endpoint available at http://localhost:{port}/sse")
    logger.info(f"Use 'mcpo --port 3003 --server-type sse -- http://localhost:{port}/sse' to connect")
    
    # Run the ASGI app
    uvicorn.run(app, host="0.0.0.0", port=port)