import streamlit as st
import asyncio
import nest_asyncio
from client3 import LangchainMCPClient
from typing import Optional, List

# Enable nested asyncio for Streamlit
nest_asyncio.apply()

# Page configuration
st.set_page_config(
    page_title="Langchain MCP Client",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'client' not in st.session_state:
    st.session_state.client = None
if 'agent_initialized' not in st.session_state:
    st.session_state.agent_initialized = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'available_tools' not in st.session_state:
    st.session_state.available_tools = []
if 'all_available_tools' not in st.session_state:
    st.session_state.all_available_tools = []
if 'selected_tool_names' not in st.session_state:
    st.session_state.selected_tool_names = []
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = None

def init_client(server_url: str):
    """Initialize the MCP client"""
    try:
        st.session_state.client = LangchainMCPClient(mcp_server_url=server_url)
        return True
    except Exception as e:
        st.error(f"Error initializing client: {str(e)}")
        return False

async def check_connection_async(client: LangchainMCPClient):
    """Async wrapper for connection check"""
    return await client.check_server_connection()

async def fetch_available_tools_async(client: LangchainMCPClient):
    """Fetch all available tools from the MCP server"""
    try:
        all_tools = await client.mcp_client.get_tools()
        return all_tools
    except Exception as e:
        st.error(f"Error fetching tools: {str(e)}")
        return []

async def initialize_agent_async(client: LangchainMCPClient, selected_tools: Optional[List[str]]):
    """Async wrapper for agent initialization"""
    await client.initialize_agent(selected_tool_names=selected_tools)
    return client.mcp_tools

async def process_message_async(client: LangchainMCPClient, user_input: str):
    """Async wrapper for message processing"""
    return await client.process_message(user_input)

def main():
    st.title("🤖 Langchain MCP Client Interface")
    st.markdown("Interact with your MCP server using Langchain and Ollama")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        server_url = st.text_input(
            "MCP Server URL",
            value="http://127.0.0.1:8000",
            help="Base URL of your MCP server (without /sse)"
        )
        
        model_name = st.text_input(
            "Ollama Model",
            value="llama3.1",
            help="Name of the Ollama model to use"
        )
        
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            help="Controls randomness in responses"
        )
        
        st.divider()
        
        # Connection section
        st.subheader("🔌 Connection")
        
        if st.button("Connect to Server", type="primary", use_container_width=True):
            with st.spinner("Connecting to MCP server..."):
                if init_client(server_url):
                    try:
                        connection_status = asyncio.run(
                            check_connection_async(st.session_state.client)
                        )
                        st.session_state.connection_status = connection_status
                        
                        if connection_status:
                            st.success("✅ Connected to server!")
                            # Fetch available tools after successful connection
                            with st.spinner("Fetching available tools..."):
                                all_tools = asyncio.run(
                                    fetch_available_tools_async(st.session_state.client)
                                )
                                st.session_state.all_available_tools = all_tools
                                # Reset agent state when reconnecting
                                st.session_state.agent_initialized = False
                                st.session_state.available_tools = []
                                # Default to all tools selected on first connection
                                if all_tools and not st.session_state.selected_tool_names:
                                    st.session_state.selected_tool_names = [tool.name for tool in all_tools]
                                if all_tools:
                                    st.success(f"Found {len(all_tools)} tool(s)")
                        else:
                            st.error("❌ Could not connect to server")
                            st.session_state.all_available_tools = []
                    except Exception as e:
                        st.error(f"Connection error: {str(e)}")
                        st.session_state.connection_status = False
                        st.session_state.all_available_tools = []
        
        # Display connection status
        if st.session_state.connection_status is not None:
            if st.session_state.connection_status:
                st.success("🟢 Connected")
            else:
                st.error("🔴 Disconnected")
        
        st.divider()
        
        # Tool selection section
        if st.session_state.connection_status and st.session_state.all_available_tools:
            st.subheader("🛠️ Tool Selection")
            
            if not st.session_state.agent_initialized:
                # Create a tool selection interface
                tool_names = [tool.name for tool in st.session_state.all_available_tools]
                tool_descriptions = {
                    tool.name: tool.description 
                    for tool in st.session_state.all_available_tools
                }
                
                st.markdown("**Select tools to enable for the agent:**")
                
                # Add "Select All" and "Deselect All" buttons
                col_select_all, col_deselect_all = st.columns(2)
                with col_select_all:
                    if st.button("✅ Select All", use_container_width=True):
                        st.session_state.selected_tool_names = tool_names.copy()
                        st.rerun()
                
                with col_deselect_all:
                    if st.button("❌ Deselect All", use_container_width=True):
                        st.session_state.selected_tool_names = []
                        st.rerun()
                
                # Multiselect for tools
                selected_tools = st.multiselect(
                    "Available Tools",
                    options=tool_names,
                    default=st.session_state.selected_tool_names if st.session_state.selected_tool_names else tool_names,
                    format_func=lambda x: f"{x} - {tool_descriptions.get(x, 'No description')[:50]}...",
                    help="Select one or more tools to enable. Selected tools will be available to the agent."
                )
                
                # Update selected tools in session state
                if selected_tools != st.session_state.selected_tool_names:
                    st.session_state.selected_tool_names = selected_tools
                
                # Display selected tools summary
                if st.session_state.selected_tool_names:
                    st.info(f"**{len(st.session_state.selected_tool_names)}** tool(s) selected")
                    with st.expander("View Selected Tools"):
                        for tool_name in st.session_state.selected_tool_names:
                            desc = tool_descriptions.get(tool_name, "No description")
                            st.markdown(f"- **{tool_name}**: {desc}")
                else:
                    st.warning("⚠️ No tools selected. Please select at least one tool.")
            else:
                # Show currently active tools when agent is initialized
                st.info(f"✅ **{len(st.session_state.available_tools)}** tool(s) active")
                with st.expander("View Active Tools"):
                    for tool in st.session_state.available_tools:
                        st.markdown(f"- **{tool.name}**: {tool.description}")
        
        st.divider()
        
        # Agent initialization section
        st.subheader("🚀 Agent Setup")
        
        if st.session_state.client is None:
            st.info("Please connect to server first")
        elif st.session_state.agent_initialized:
            st.success("✅ Agent initialized")
            if st.button("Reset Agent", use_container_width=True):
                st.session_state.agent_initialized = False
                st.session_state.chat_history = []
                st.session_state.available_tools = []
                # Keep selected_tool_names so user can easily re-initialize with same selection
                st.rerun()
        else:
            if st.button("Initialize Agent", type="primary", use_container_width=True):
                if st.session_state.connection_status:
                    # Check if tools are selected
                    if not st.session_state.selected_tool_names:
                        st.warning("⚠️ Please select at least one tool before initializing the agent.")
                    else:
                        with st.spinner(f"Initializing agent with {len(st.session_state.selected_tool_names)} tool(s)..."):
                            try:
                                # Pass selected tool names to agent initialization
                                tools = asyncio.run(
                                    initialize_agent_async(
                                        st.session_state.client, 
                                        st.session_state.selected_tool_names
                                    )
                                )
                                st.session_state.available_tools = tools
                                st.session_state.agent_initialized = True
                                st.success(f"✅ Agent initialized with {len(tools)} tool(s)")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error initializing agent: {str(e)}")
                else:
                    st.warning("Please connect to server first")
        
        st.divider()
        
        # Tools display
        if st.session_state.available_tools:
            st.subheader("🛠️ Available Tools")
            for tool in st.session_state.available_tools:
                with st.expander(f"📌 {tool.name}"):
                    st.write(f"**Description:** {tool.description}")
                    if hasattr(tool, 'args_schema') and tool.args_schema:
                        st.write("**Parameters:**")
                        st.json(tool.args_schema.schema() if hasattr(tool.args_schema, 'schema') else str(tool.args_schema))
        
        st.divider()
        
        # Clear chat button
        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat History", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Chat")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for i, message in enumerate(st.session_state.chat_history):
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])
        
        # Chat input
        if st.session_state.agent_initialized:
            user_input = st.chat_input("Type your message here...")
            
            if user_input:
                # Add user message to history
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_input
                })
                
                # Process message
                with st.spinner("Processing..."):
                    try:
                        response = asyncio.run(
                            process_message_async(st.session_state.client, user_input)
                        )
                        
                        # Add assistant response to history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response
                        })
                        
                        st.rerun()
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": error_msg
                        })
                        st.rerun()
        else:
            st.info("👆 Please initialize the agent in the sidebar to start chatting")
    
    with col2:
        st.header("ℹ️ Information")
        
        st.subheader("Status")
        if st.session_state.client is None:
            st.warning("Client not initialized")
        elif st.session_state.connection_status is None:
            st.info("Connection status unknown")
        elif st.session_state.connection_status:
            st.success("🟢 Connected")
        else:
            st.error("🔴 Disconnected")
        
        if st.session_state.agent_initialized:
            st.success(f"Agent ready with {len(st.session_state.available_tools)} tool(s)")
        else:
            st.info("Agent not initialized")
        
        st.divider()
        
        st.subheader("📋 Instructions")
        st.markdown("""
        1. **Configure** the MCP server URL in the sidebar
        2. **Connect** to the server
        3. **Initialize** the agent to load available tools
        4. **Start chatting** with the agent
        
        The agent can use the available MCP tools to help answer your questions.
        """)
        
        st.divider()
        
        if st.session_state.chat_history:
            st.subheader("📊 Chat Stats")
            st.metric("Messages", len(st.session_state.chat_history))
            user_messages = len([m for m in st.session_state.chat_history if m["role"] == "user"])
            st.metric("User Messages", user_messages)

if __name__ == "__main__":
    main()

