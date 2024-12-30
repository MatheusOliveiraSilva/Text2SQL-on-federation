from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import START, StateGraph, MessagesState
from langchain_core.messages import HumanMessage
from nodes import assistant
import tools as t

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
graph = builder.compile()

if __name__ == "__main__":
    messages = [HumanMessage(
        content="Quais aeroportos estão localizados em países da América do Norte e qual o tipo de governo desses países?")
    ]
    result = graph.invoke({"messages": messages})

    for message in result["messages"]:
        print(message.content)
        print("-" * 50)
