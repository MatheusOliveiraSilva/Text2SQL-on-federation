import re
import os
import sys
import json
import llm_as_judge.tools as tools
import llm_as_judge.prompts as prompts
import langchain
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from llm_utils.langchain_utils import get_llm
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage
from schemas.mondial_federated_schema import MONDIAL_FULL_SCHEMA, MONDIAL_POlITICS, MONDIAL_GEO, MONDIAL_ECONOMY, MONDIAL_SOCIAL

load_dotenv()
llm = get_llm()

def assistant(state: MessagesState):
    """
    This function representes the single node on graph, is a ReAct assistant.
    He gives a query to another LLM and reason about it.
    """

    llm_tools = [
        tools.interact_with_agent
    ]

    llm_with_tools = llm.bind_tools(llm_tools)

    sys_msg = SystemMessage(
        content=prompts.ASSISTANT_PROMPT.format(
            input=state["messages"][-1].content,
            geo_db_schema=MONDIAL_GEO,
            economy_db_schema=MONDIAL_ECONOMY,
            social_db_schema=MONDIAL_SOCIAL,
            politics_db_schema=MONDIAL_POlITICS
        )
    )

    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}
