"""
agent.py - Core AI Brain of the CRM

PURPOSE:
This module defines the 'Human-in-the-loop' AI Agent using LangGraph and LangChain. 
It creates a conversational workflow that:
1. Interacts with the user to gather missing interaction details (HCP Name, Date, Sentiment).
2. Uses the Groq LLM to parse and formulate responses.
3. Automatically triggers relevant tools (like saving to a database) ONLY when all required data is collected.

HOW IT WORKS AT A GLANCE:
- StateGraph: Manages the memory and flow of the conversation.
- System Prompt: Gives the LLM strict instructions on its personality, rules, and how to format JSON output.
- ToolNode: Exposes backend Python functions (tools) to the LLM so it can execute them when appropriate.
"""
import os
from typing import Annotated, TypedDict
from dotenv import load_dotenv

# LangChain & LangGraph imports for defining the LLM and the computational graph
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# Import our custom business logic tools
from tools import search_hcp, log_interaction, edit_interaction, schedule_follow_up, generate_summary

# 1. INITIALIZATION
# Load environment variables (e.g., GROQ_API_KEY) from .env file
load_dotenv()

# Initialize the Groq LLM. 
# Temperature is 0 to ensure deterministic, highly predictable outputs (crucial for tool calling & JSON generation).
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

# 2. BIND TOOLS
# Give the LLM knowledge of our database operations.
tools_list = [search_hcp, log_interaction, edit_interaction, schedule_follow_up, generate_summary]
llm_with_tools = llm.bind_tools(tools_list)

# 3. DEFINE STATE
# The State represents the memory of the conversation. 
# `add_messages` ensures new messages are appended rather than overwriting old ones.
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# 4. DEFINE SYSTEM PROMPT
# This is the core instruction set for the AI. It forces the AI to be a strict data-gatherer.
SYSTEM_PROMPT = SystemMessage(content=(
    "You are a 'Human-in-the-loop' CRM Agent. Your goal is to ensure the Log Interaction form is 100% complete.\n\n"
    "CRITICAL RULES:\n"
    "1. HISTORY CHECK: Read the ENTIRE conversation history. If the user ALREADY provided a name, date, or sentiment in a previous message, DO NOT ask for it again.\n"
    "2. MISSING INFO: If essential info (HCP Name, Date, Sentiment) is still missing, ask for it naturally.\n"
    "3. ABSOLUTE TOOL BAN: You are in the DATA GATHERING phase. DO NOT call ANY tools or functions whatsoever (no search_hcp, no log_interaction, etc.) until the form is 100% complete. Just ask the user for the missing info.\n"
    "4. DATE LOGIC: If the user says 'yesterday', calculate the exact YYYY-MM-DD based on 'Today is April 24, 2026'.\n"
    "5. UI GAG RULE: You must NEVER announce the JSON block. Do NOT use phrases like 'Here is the JSON block' or 'Here's what I have'. Provide your conversational response, and then append the JSON completely silently.\n\n"
    "JSON FORMATTING RULE:\n"
    "You MUST wrap the JSON block in triple backticks and include the word 'json'.\n"
    "Example:\n"
    "```json\n"
    "{\n"
    "  \"hcpName\": \"...\",\n"
    "  \"interactionType\": \"...\",\n"
    "  \"sentiment\": \"...\",\n"
    "  \"date\": \"...\",\n"
    "  \"topics\": \"...\"\n"
    "}\n"
    "```\n"
    "If you do not use the triple backticks, the user's form will not fill. This is mandatory."
))

# 5. DEFINE GRAPH NODES
def chatbot(state: State):
    """
    The main decision-making node. 
    It prepends the System Prompt to the conversation history so the LLM always remembers its instructions.
    """
    full_messages = [SYSTEM_PROMPT] + state["messages"]
    response = llm_with_tools.invoke(full_messages)
    return {"messages": [response]}

# 6. BUILD GRAPH
# StateGraph orchestrates the cyclic flow: User -> LLM -> Tools -> LLM ...
graph_builder = StateGraph(State)

# Add the primary chatbot node
graph_builder.add_node("chatbot", chatbot)

# Add the ToolNode which executes the python functions if the LLM requests it
tool_node = ToolNode(tools=tools_list)
graph_builder.add_node("tools", tool_node)

# Define routing logic: 
# If the LLM output includes a tool call -> go to 'tools' node.
# Otherwise -> END the graph execution and return the final response to the user.
graph_builder.add_conditional_edges(
    "chatbot",
    lambda state: "tools" if state["messages"][-1].tool_calls else END,
)

# After a tool executes, ALWAYS loop back to the chatbot so the LLM can interpret the tool's result.
graph_builder.add_edge("tools", "chatbot")

# Start point
graph_builder.add_edge(START, "chatbot")

# Compile into an executable agent
agent_executor = graph_builder.compile()