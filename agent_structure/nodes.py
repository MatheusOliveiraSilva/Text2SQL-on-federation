import re
import os
import sys
import json
import agent_structure.tools as tools
import agent_structure.prompts as prompts
import langchain
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from llm_utils.langchain_utils import get_llm
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage
from agent_structure.schemas.mondial_federated_schema import MONDIAL_FULL_SCHEMA

load_dotenv()
llm = get_llm()

def assistant(state: MessagesState):
    """
    This function representes the single node on graph, is a ReAct assistant.
    He receives a query, decides if it is a NL question about database or not and returns a response
    based on that. If is a question about database, it decomposes the question into subqueries and
    joins them together.
    """

    llm_tools = [
        tools.get_relevant_tables,
        tools.get_subqueries,
        tools.join_subqueries
    ]

    llm_with_tools = llm.bind_tools(llm_tools)

    prompt_with_schema = prompts.ASSISTANT_PROMPT.replace("{schema}", MONDIAL_FULL_SCHEMA)

    sys_msg = SystemMessage(
        content=prompt_with_schema.format(input=state["messages"][-1].content)
    )

    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}
