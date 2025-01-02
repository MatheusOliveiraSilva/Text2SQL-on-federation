from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import START, StateGraph, MessagesState
from langchain_core.messages import HumanMessage
from agent_structure.nodes import assistant
import agent_structure.tools as t
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

tools = [
    t.get_relevant_tables,
    t.get_subqueries,
    t.join_subqueries
]

# Build graph
builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")

# Compile graph
graph = builder.compile(checkpointer=memory)

if __name__ == "__main__":
    messages = [HumanMessage(
        content="Quais aeroportos estão localizados em países da América do Norte e qual o tipo de governo desses países?")
    ]
    result = graph.invoke({"messages": messages})

    print(result)
