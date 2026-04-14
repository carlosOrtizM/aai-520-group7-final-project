"""LangGraph RAG pipeline.

Ported from g(old)/session_init/rag_builder.py. Retrieves chunks from
the Chroma vector store with a tool-call, then synthesizes an answer
using the Ollama LLM. The graph is cached at module level — building
it is cheap, but invoking ``vector_store.similarity_search`` requires
both Ollama and Chroma to be reachable.
"""

_RAG_GRAPH = None


def get_rag_graph():
    """Build (or reuse) the compiled RAG LangGraph."""
    global _RAG_GRAPH
    if _RAG_GRAPH is not None:
        return _RAG_GRAPH

    from langchain_core.tools import tool
    from langgraph.graph import END, MessagesState, StateGraph
    from langgraph.prebuilt import ToolNode, tools_condition

    from src.agent.chroma_store import get_vector_store
    from src.agent.llm_loader import get_llm_client

    vector_store = get_vector_store()
    llm = get_llm_client()

    @tool(response_format="content_and_artifact")
    def retrieve(query: str):
        """Retrieve information related to a query."""
        retrieved_docs = vector_store.similarity_search(query, k=5)
        serialized = "\n\n".join(
            f"Source: {doc.metadata}\nContent: {doc.page_content}"
            for doc in retrieved_docs
        )
        return serialized, retrieved_docs

    def query_or_respond(state: MessagesState):
        llm_with_tools = llm.bind_tools([retrieve])
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    tools_node = ToolNode([retrieve])

    def generate(state: MessagesState):
        recent_tool_messages = []
        for message in reversed(state["messages"]):
            if message.type == "tool":
                recent_tool_messages.append(message)
            else:
                break

        conversation_messages = [
            message.content
            for message in state["messages"]
            if message.type in ("human", "system")
            or (message.type == "ai" and not message.tool_calls)
        ]

        prompt = (
            "As an experienced financial advisor analyzing AAPL trends, "
            "answer the user's question using the retrieved 10-K context "
            "below. If the context is insufficient, say so plainly — do "
            "not fabricate.\n\n"
            f"User question: {conversation_messages}\n\n"
            f"Retrieved context: {recent_tool_messages}\n"
        )
        response = llm.invoke([prompt])
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("query_or_respond", query_or_respond)
    builder.add_node("tools", tools_node)
    builder.add_node("generate", generate)
    builder.set_entry_point("query_or_respond")
    builder.add_conditional_edges(
        "query_or_respond",
        tools_condition,
        {END: END, "tools": "tools"},
    )
    builder.add_edge("tools", "generate")
    builder.add_edge("generate", END)

    _RAG_GRAPH = builder.compile()
    return _RAG_GRAPH


async def run_rag_query(query: str) -> dict:
    """Invoke the RAG graph with a single user query."""
    from langchain_core.messages import HumanMessage

    graph = get_rag_graph()
    state = await graph.ainvoke({"messages": [HumanMessage(content=query)]})
    final = state["messages"][-1]
    return {
        "answer": getattr(final, "content", str(final)),
        "n_messages": len(state["messages"]),
    }
