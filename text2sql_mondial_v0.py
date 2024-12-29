from paths import *
from langchain_openai import ChatOpenAI

import langchain
from langchain.chains import LLMChain
from pathlib import Path

from dotenv import load_dotenv
import os
import sys

import pandas as pd

from functions.retrieval import QuestionRetriever
from functions.sql_query_chain_view_functions import SQLQueryChainViewFunction
from functions.query_decomposer import QueryDecomposer
from functions.SchemaLinkerDanke import SchemaLinkerDanke
from functions.DankeSchema import DankeSchema
from functions.text_to_sql import TextToSQL
from functions.Question_Rewriter import Question_Rewriter
from functions.dataset_utils import DatasetEvaluator
from langchain_core.messages import SystemMessage, HumanMessage

import json
import re

from langchain_core.messages import SystemMessage

from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode


entities = [
    "Airport",
    "Borders",
    "City",
    "City other name",
    "Continent",
    "Country",
    "Desert",
    "Economy",
    "Encompasses",
    "Ethnic Group",
    "Geo desert",
    "Geo estuary",
    "Geo island",
    "Geo lake",
    "Geo mountain",
    "Geo river",
    "Geo sea",
    "Geo source",
    "Island",
    "Is member",
    "Lake",
    "Language",
    "Mountain",
    "Mountain on island",
    "Organization",
    "Politics",
    "Population",
    "Province",
    "Province other name",
    "Province population",
    "Religion",
    "River",
    "River through",
    "Sea"
]

# ------ setup da tool de text to SQL ------

llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

with open(DB_CONNECTION_FILE, "r") as file:
    db_connections = json.load(file)

retriever = QuestionRetriever(
    dataset_path=DATASET_SYNTHETIC_PATH,
    vectors_path=EMBEDDINGS_PATH,
    environment=""
)
retriever.remove_duplicates()

danke_schema = DankeSchema("mondial", db_connections)

def get_model():
    return ChatOpenAI(model="gpt-4o", temperature=0.7)

# Decomposição
decomposer_4o = QueryDecomposer(
    get_model(),
    PROMPT_DECOMPOSER_FILE,
    False
)

# Schema Linking - Com colunas e com escopo reduzido
schema_linker_4o = SchemaLinkerDanke(
    get_model(),
    PROMPT_SCHEMA_LINKING_FILE,
    danke_schema,
    use_columns=True,
    list_entities=entities
)

# Funções para views
view_functions = SQLQueryChainViewFunction(
    SCHEMA, PREFIX, None, PROMPT_FILE,
    dataset_eval=dataset_eval,
    retriever=retriever
)

# LLM Chain Text-to-SQL
llm_chain_convert_query = LLMChain(
    llm=get_model(),
    prompt=view_functions.get_prompt(),
    verbose=False
)

text_to_sql_module = TextToSQL(
    sql_query_chain_view_function=view_functions,
    llm_chain_convert_query=llm_chain_convert_query,
    danke_schema=danke_schema,
    schema_linker_module=schema_linker_4o,
    decomposer_module=decomposer_4o,
    debug=False
)

def execute_sql_query(sql_query, limit=3):
    try:
        if not "FETCH FIRST" in sql_query:
            sql_query = sql_query.replace(";", f" FETCH FIRST {limit} ROWS ONLY;")

        if "DISTINCT" in sql_query:
            sql_query = sql_query.replace("DISTINCT", "")

        # print(sql_query)
        result = dataset_eval.run_sql_query(sql_query)
        # result = '''
        #     prop, value, description
        #     p-1, as, asasasasa
        #     p-2, as, saddds
        #     p-3, cd, asasas
        # '''
        return result
    except Exception as e:
        return str(e)

# ------ setup do LangGraph ------

# Tool do agente ReAct.
def convert_text_to_sql_and_execute(query) -> str:
    """
    Converts a natural language query to an SQL query based on the current database schema and execute the sql
    generated on database.
    Args:
        query (str): natural language query.
    """
    try:
        sql_query = text_to_sql_module.run_experiment_complete(query, debug=False)
        print(sql_query["query_string_danke_view"])
        return execute_sql_query(sql_query["query_string"])
    except Exception as e:
        return str(e)

tools = [convert_text_to_sql_and_execute]

llm_with_tools = llm.bind_tools(tools)

assistant_prompt = """
# You are a chatbot agent that responds to user questions about a database.

# Rules:
First, verify if the question is related to the database.
!! Identifier is used to link tables, like name of countrys, cities etc !!!
If it is, determine whether the question needs to be rewritten.
If so, enrich the question with relevant data from the conversation history. Otherwise, use the original question for the next step.
Next, invoke the tool that converts natural language questions to SQL and executes it on the database.
Finally, return the result.

# Attention:
If an error occurs, apologize to the user and ask them to rephrase the question for better clarity.
Do not attempt to convert the user’s question to SQL; this is the tool's responsibility.

# The database schema is provided below. If the user asks a question outside the schema’s scope, apologize and inform them that it is beyond your scope.
{schema}

# Pergunta do usuário: {input}
"""

prompt_with_schema = assistant_prompt.replace("{schema}", schema_linker_4o.get_schema_to_link_prompt())

def assistant(state: MessagesState):
    sys_msg = SystemMessage(
        content=prompt_with_schema.format(input=state["messages"][-1].content)
    )

    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

# Build graph
builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", "assistant")

# Compile graph
graph = builder.compile()

messages = [HumanMessage(content="What is the average number of airports per country?")]
result = graph.invoke({"messages": messages})

print("\n"*50)
print(result)
