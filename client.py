from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
# from langchain_groq import ChatGroq
from langchain_ollama import OllamaLLM
import ollama
from llama_index.llms.ollama import Ollama
# from dotenv import load_dotenv
# load_dotenv()

import asyncio

async def main():
    client=MultiServerMCPClient(
        {
            "math":{
                "command":"python",
                "args":["mathserver.py"], ## Ensure correct absolute path
                "transport":"stdio",
            
            },
            "weather": {
                "url": "http://localhost:8000/mcp",  # Ensure server is running here
                "transport": "streamable_http",
            }

        }
    )

    # import os
    # os.environ["GROQ_API_KEY"]=os.getenv("GROQ_API_KEY")

    tools=await client.get_tools()
    # model=ChatGroq(model="qwen/qwen3-32b")
    # model = ollama.create(model='weather api', from_="llama3.2:1b")
    model = Ollama(model="llama3.2:1b", request_timeout=120.0)

    agent=create_agent(
        model,tools
    )

    # math_response = await agent.ainvoke(
    #     {"messages": [{"role": "user", "content": "what's (3 + 5) x 12?"}]}
    # )

    # print("Math response:", math_response['messages'][-1].content)

    weather_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what is the weather in Los Angeles?"}]}
    )
    print("Weather response:", weather_response['messages'][-1].content)

asyncio.run(main())


# import asyncio
# from typing import Optional
# from contextlib import AsyncExitStack

# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client

# from anthropic import Anthropic
# from dotenv import load_dotenv

# load_dotenv()  # load environment variables from .env

# # Claude model constant
# ANTHROPIC_MODEL = "qwen/qwen3-32b"

# class MCPClient:
#     def __init__(self):
#         # Initialize session and client objects
#         self.session: Optional[ClientSession] = None
#         self.exit_stack = AsyncExitStack()
#         self.anthropic = Anthropic()

#     async def connect_to_server(self, server_script_path: str):
#         """Connect to an MCP server
        
#         Args:
#             server_script_path: Path to the server script (.py or .js)
#         """
#         is_python = server_script_path.endswith('.py')
#         is_js = server_script_path.endswith('.js')
#         if not (is_python or is_js):
#             raise ValueError("Server script must be a .py or .js file")
            
#         command = "python" if is_python else "node"
#         server_params = StdioServerParameters(
#             command=command,
#             args=[server_script_path],
#             env=None
#         )
        
#         stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
#         self.stdio, self.write = stdio_transport
#         self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
#         await self.session.initialize()
        
#         # List available tools
#         response = await self.session.list_tools()
#         tools = response.tools
#         print("\nConnected to server with tools:", [tool.name for tool in tools])

#     async def process_query(self, query: str) -> str:
#         """Process a query using Claude and available tools"""
#         messages = [
#             {
#                 "role": "user",
#                 "content": query
#             }
#         ]

#         response = await self.session.list_tools()
#         available_tools = [{ 
#             "name": tool.name,
#             "description": tool.description,
#             "input_schema": tool.inputSchema
#         } for tool in response.tools]

#         # Initial Claude API call
#         response = self.anthropic.messages.create(
#             model=ANTHROPIC_MODEL,
#             max_tokens=1000,
#             messages=messages,
#             tools=available_tools
#         )

#         # Process response and handle tool calls
#         final_text = []

#         for content in response.content:
#             if content.type == 'text':
#                 final_text.append(content.text)
#             elif content.type == 'tool_use':
#                 tool_name = content.name
#                 tool_args = content.input
                
#                 # Execute tool call
#                 result = await self.session.call_tool(tool_name, tool_args)
#                 final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

#                 # Continue conversation with tool results
#                 if hasattr(content, 'text') and content.text:
#                     messages.append({
#                       "role": "assistant",
#                       "content": content.text
#                     })
#                 messages.append({
#                     "role": "user", 
#                     "content": result.content
#                 })

#                 # Get next response from Claude
#                 response = self.anthropic.messages.create(
#                     model=ANTHROPIC_MODEL,
#                     max_tokens=1000,
#                     messages=messages,
#                 )

#                 final_text.append(response.content[0].text)

#         return "\n".join(final_text)

#     async def chat_loop(self):
#         """Run an interactive chat loop"""
#         print("\nMCP Client Started!")
#         print("Type your queries or 'quit' to exit.")
        
#         while True:
#             try:
#                 query = input("\nQuery: ").strip()
                
#                 if query.lower() == 'quit':
#                     break
                    
#                 response = await self.process_query(query)
#                 print("\n" + response)
                    
#             except Exception as e:
#                 print(f"\nError: {str(e)}")
    
#     async def cleanup(self):
#         """Clean up resources"""
#         await self.exit_stack.aclose()

# async def main():
#     if len(sys.argv) < 2:
#         print("Usage: python client.py <path_to_server_script>")
#         sys.exit(1)
        
#     client = MCPClient()
#     try:
#         await client.connect_to_server(sys.argv[1])
#         await client.chat_loop()
#     finally:
#         await client.cleanup()

# if __name__ == "__main__":
#     import sys
#     asyncio.run(main())