import re
import os
import sys
import json
import langchain
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from langchain.chains import LLMChain
from text2sql_mondial_v1 import graph as agent
import llm_as_judge.prompts as prompts
from langchain_openai import ChatOpenAI
from llm_utils.langchain_utils import get_llm
from langchain_core.output_parsers import StrOutputParser
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import START, StateGraph, MessagesState
from langchain_core.messages import SystemMessage, HumanMessage
from schemas.mondial_federated_schema import MONDIAL_ECONOMY, MONDIAL_GEO, MONDIAL_POlITICS, MONDIAL_SOCIAL, MONDIAL_FULL_SCHEMA

load_dotenv()
llm = get_llm()

with open("dataset/federated_mondial_dataset.json", "r") as f:
    dataset = json.load(f)

DATASET = dataset["dataset"]

def evaluate_tables_retrieved(retrieved_tables: str) -> str:
    """
    Function that evaluates the retrieved tables.
    Args:
        retrieved_tables (str):
    """

    return ""

def evaluate_subqueries_retrieved(retrieved_subqueries: str) -> str:
    """
    Function that evalute subqueries that model generated.
    Args:
        retrieved_subqueries (str):
    """

    # TODO

    return ""

def evalute_integration_plan(integration_plan: str) -> str:
    """
    Function that evaluates the integration plan.
    Args:
        integration_plan (str):
    """

    # TODO

    return ""

def evaluate_all_agent_interactions(all_agent_interactions: str) -> str:
    """
    Function that evaluates the all agent interactions.
    Args:
        all_agent_interactions (str):
    """

    # TODO

    return ""

def interact_with_agent(identifier: str) -> str:
    """
    Function that interacts with the agent.
    Args:
        identifier (str): Identifier of the example.
    """

    example = DATASET[int(identifier)]

    config = {"configurable": {"thread_id": example["id"]}}

    result = agent.invoke({"messages": [HumanMessage(content=example["question"])]}, config)
    
    result = agent.invoke({"messages": [HumanMessage(content="Yes sure.")]}, config)

    return result

