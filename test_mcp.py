import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.agents.utils.agent_utils import Toolkit

def test_mcp_connection():
    """Tests the MCP connection by performing a simple web search."""
    print("--- Testing MCP Connection ---")
    try:
        result = Toolkit.search_web_with_mcp(
            query="Test query for MCP connection",
            max_results=1
        )
        print("MCP Connection Successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"MCP Connection Failed: {e}")

if __name__ == "__main__":
    test_mcp_connection()
