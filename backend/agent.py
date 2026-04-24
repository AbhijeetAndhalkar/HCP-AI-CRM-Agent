import os
from typing import Annotated, TypedDict
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv

# Ensure these tools are correctly imported from your tools.py
from tools import search_hcp, log_interaction, edit_interaction, schedule_follow_up, generate_summary

# Load environment variables
load_dotenv()

# Initialize LLM with the compliant model from the assignment doc
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

# Bind tools
tools_list = [search_hcp, log_interaction, edit_interaction, schedule_follow_up, generate_summary]
llm_with_tools = llm.bind_tools(tools_list)

# Define State
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

from langchain_core.messages import SystemMessage

from langchain_core.messages import SystemMessage

# --- THE SYSTEM PROMPT ---
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
# Define nodes
def chatbot(state: State):
    # Combine the system prompt with the conversation history
    full_messages = [SYSTEM_PROMPT] + state["messages"]
    response = llm_with_tools.invoke(full_messages)
    return {"messages": [response]}

# Build Graph
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=tools_list)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    lambda state: "tools" if state["messages"][-1].tool_calls else END,
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

agent_executor = graph_builder.compile()