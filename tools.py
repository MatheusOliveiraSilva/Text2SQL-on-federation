import re
import os
import sys
import json
import prompts
import langchain
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from langchain_utils import get_llm
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import START, StateGraph, MessagesState
from langchain_core.messages import SystemMessage, HumanMessage
from schemas.mondial_federated_schema import MONDIAL_ECONOMY, MONDIAL_GEO, MONDIAL_POlITICS, MONDIAL_SOCIAL, MONDIAL_FULL_SCHEMA

load_dotenv()
llm = get_llm()

def retrieve_relevant_sameastable_relations(relevant_tables: list) -> str:
    """
    Retrieve relevant same-as-table relations based on the provided list of relevant tables.
    Args:
        relevant_tables (list): A list of relevant table names.
    """

    SameAsTable_path = "schemas/consolidated_sameastable.json"

    with open(SameAsTable_path) as f:
        same_as_table_json = json.load(f)

    relevant_relations = []

    for relation in same_as_table_json:
        is_relevant = (
                (relation['Class Source'] in relevant_tables)
                or
                (relation['Class Destination'] in relevant_tables)
        )

        if is_relevant:
            relevant_relations.append(relation)

    final_relations = ""
    for relation in relevant_relations:
        relation = json.dumps(relation)
        final_relations += relation + "\n"

    return final_relations


def get_relevant_tables(question: str) -> list:
    """
    Retrieve the relevant tables based on the user's question.
    Args:
        question (str): The user's question.
    """

    chain = llm | StrOutputParser()

    relevant_tables = chain.invoke(prompts.RELEVANT_TABLE_PROMPT.format(schema=MONDIAL_FULL_SCHEMA, question=question))

    # convert relevant tables in a list of strings
    relevant_tables = relevant_tables.split(", ")
    return relevant_tables

def get_subqueries(query: str, relevant_tables: list) -> str:
    """
    Generate subqueries for each federated schema based on the user's query.
    Args:
        query (str): The user's query.
        relevant_tables (list): The SameAsTable relationships between tables across schemas.
    """

    prompt = prompts.SUBQUERY_PROMPT.format(
        economy_schema=MONDIAL_ECONOMY,
        social_schema=MONDIAL_SOCIAL,
        geo_schema=MONDIAL_GEO,
        politics_schema=MONDIAL_POlITICS,
        same_as_table=retrieve_relevant_sameastable_relations(relevant_tables),
        query=query
    )

    human_msg = HumanMessage(
        content=prompt
    )

    chain = llm | StrOutputParser()
    result = chain.invoke([human_msg])

    return result

def join_subqueries(subqueries: str, relevant_tables: list) -> str:
    """
    Join the subqueries for each federated schema into a single query, form the integration prompt using the
    consolidated data that consists on SameAsTable.
    Args:
        subqueries (str): The subqueries for each federated schema.
        relevant_tables (list): The relevant tables from the user's question, returned by get_relevant_tables.
    """
    prompt = prompts.INTEGRATION_PROMPT.format(
        subqueries=subqueries,
        same_as_table=retrieve_relevant_sameastable_relations(relevant_tables)
    )

    human_msg = HumanMessage(
        content=prompt
    )

    chain = llm | StrOutputParser()
    result = chain.invoke([human_msg])

    return result

