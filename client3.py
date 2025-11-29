import asyncio
import nest_asyncio
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
# from langchain_core.memory import ConversationBufferMemory
from langchain_mcp_adapters.tools import MCPTool
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import httpx
from typing import Optional, Any, Callable, Awaitable

# Enable nested asyncio for Jupyter-like environments
nest_asyncio.apply()

REACT_TEMPLATE = """Answer the following questions as best you can. You have access to the following tools:
"""

class LangchainMCPClient:
    def __init__(self, mcp_server_url="http://127.0.0.1:8000"):
        print("Initializing LangchainMCPClient...")
        self.llm = ChatOllama(
            model="llama3.1",
            temperature=0.7
        )
        
        server_config = {
            "default": {
                "url": f"{mcp_server_url}/sse",
                "transport": "sse"
            }
        }
        print(f"Connecting to MCP server at {mcp_server_url}...")
        self.mcp_client = MultiServerMCPClient(server_config)

        # self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        # self.chat_history = []
        
        # System prompt for the agent
        self.SYSTEM_PROMPT = """
                You are an AI assistant that helps users interact with a Github repository Earmark-service.
                You can communicate with the MCP server configured in the URL given and return a response
        """

    async def check_server_connection(self):
        """Check if the MCP server is accessible"""
        base_url = self.mcp_client.connections["default"]["url"].replace("/sse", "")
        try:
            print(f"Testing connection to {base_url}...")
            async with httpx.AsyncClient(timeout=5.0) as client:  # Shorter timeout
                # Try the SSE endpoint directly
                sse_url = f"{base_url}/sse"
                print(f"Checking SSE endpoint at {sse_url}...")
                response = await client.get(sse_url, timeout=5.0)
                print(f"Got response: {response.status_code}")
                if response.status_code == 200:
                    print("SSE endpoint is accessible!")
                    return True
                
                print(f"Server responded with status code: {response.status_code}")
                return False
                
        except httpx.ConnectError:
            print(f"Could not connect to server at {base_url}")
            print("Please ensure the server is running and the port is correct")
            return False
        except httpx.ReadTimeout:
            print("Connection established but timed out while reading")
            print("This is normal for SSE connections - proceeding...")
            return True
        except Exception as e:
            print(f"Error connecting to MCP server: {type(e).__name__} - {str(e)}")
            return False

    async def initialize_agent(self, selected_tool_names: Optional[list] = None):
        """Initialize the agent with tools and prompt template
        
        Args:
            selected_tool_names: Optional list of tool names to use. If None, all tools are used.
        """
        print("\nInitializing agent...")
        if not await self.check_server_connection():
            raise ConnectionError("Cannot connect to MCP server. Please ensure the server is running.")
            
        try:
            print("Getting available tools...")
            all_tools = await self.mcp_client.get_tools()
            
            # Filter tools if selected_tool_names is provided
            if selected_tool_names and len(selected_tool_names) > 0:
                tool_name_map = {tool.name: tool for tool in all_tools}
                self.mcp_tools = [
                    tool_name_map[name] 
                    for name in selected_tool_names 
                    if name in tool_name_map
                ]
                if len(self.mcp_tools) != len(selected_tool_names):
                    missing = set(selected_tool_names) - set(tool.name for tool in self.mcp_tools)
                    print(f"Warning: Some selected tools were not found: {missing}")
            else:
                # Use all tools if no selection provided
                self.mcp_tools = all_tools
            
            # Verify tools are properly initialized
            print("Verifying tools...")
            for i, tool in enumerate(self.mcp_tools):
                print(f"\nTool {i+1}:")
                print(f"  Name: {tool.name if hasattr(tool, 'name') else 'No name'}")
                print(f"  Description: {tool.description if hasattr(tool, 'description') else 'No description'}")
            
            # Create the agent with simpler configuration
            self.agent = create_agent(
                self.llm,
                self.mcp_tools
                # memory=self.memory
            )
            
            print(f"\nAgent reinitialized using {len(self.mcp_tools)} tool(s)")
                
        except Exception as e:
            print(f"\nError initializing agent: {e}")
            raise

    async def process_message(self, user_input: str) -> str:
        """Process a single user message and return the agent's response"""
        try:
            print("\nProcessing message:", user_input)
            # Execute the agent
            response = await self.agent.ainvoke({
                "messages": [
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
            })
            
            # Extract the final response from the messages
            final_response = response['messages'][-1].content
            print("\nRaw response:", final_response)
            return final_response
            
        except Exception as e:
            error_msg = f"Error processing message: {type(e).__name__} - {str(e)}\nPlease try rephrasing your request."
            print(f"\nError processing message: {type(e).__name__} - {str(e)}")
            print(f"Full error: {e.__dict__}")
            return error_msg

    async def interactive_chat(self):
        """Start an interactive chat session"""
        print("Chat session started. Type 'exit' to quit.")
        
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() == "exit":
                print("Ending chat session...")
                break
            
            response = await self.process_message(user_input)
            print("\nAgent:", response)

async def main():
    try:
        print("Starting Langchain MCP Client...")
        client = LangchainMCPClient()
        
        print("\nInitializing agent...")
        await client.initialize_agent()
        
        print("\nStarting interactive chat...")
        await client.interactive_chat()
        
    except ConnectionError as e:
        print(f"\nConnection Error: {e}")
        print("Please check that:")
        print("1. The MCP server is running (python server.py --server_type=sse)")
        print("2. The server URL is correct (http://127.0.0.1:8000)")
        print("3. The server is accessible from your machine")
    except Exception as e:
        print(f"\nUnexpected error: {type(e).__name__} - {str(e)}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 