from langgraph.graph import MessagesState, StateGraph
from langgraph.graph import END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from utilities.metric_utils import basic_logger

# This initial graph is a simple demo RAG prompt-chain pipeline that fetches documents from the vector store and returns
# and generates an answer based upon the user prompt + the retrieved documents.
# # retrieved_docs = vector_store.similarity_search(query, k=3)

@basic_logger
def graph_builder(vector_store, llm):
    """This function creates a LangGraph workflow. It contains the corresponding functions, tools, and models that
    are used by the model in order to execute successfully."""

    # Internal States and Base Models

    # Tools available for the graph.
    @tool(response_format="content_and_artifact")
    def retrieve(query: str):
        """Retrieve information related to a query."""
        retrieved_docs = vector_store.similarity_search(query, k=5)
        [print(f"Documents retrieved: {doc.page_content}\n") for doc in retrieved_docs]

        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\nContent: {doc.page_content}")
            for doc in retrieved_docs
        )
        return serialized, retrieved_docs

    # Functions that act as nodes, conditional edges, triggers, or internal functions in the graph.

    # Step 1: Generate an AIMessage that may include a tool-call to be sent.
    def query_or_respond(state: MessagesState):
        """Generate tool call for retrieval or respond."""
        try:
            llm_with_tools = llm.bind_tools([retrieve])
            response = llm_with_tools.invoke(state["messages"])

            # MessagesState appends messages to state instead of overwriting
            return {"messages": [response]}
        except Exception as e:
            print(f"Error {e} generating the RAG tool call.")

    # Step 2: Execute the retrieval.
    tools = ToolNode([retrieve])

    # Step 3: Generate a response using the retrieved content.
    def generate(state: MessagesState):
        """Generate answer based on the retrieved docs."""
        try:
            # Get generated ToolMessages
            recent_tool_messages = []

            for message in reversed(state["messages"]):
                # Tool messages
                if message.type == "tool":
                   recent_tool_messages.append(message)

                else:
                    break

            #tool_messages = recent_tool_messages[::-1]

            conversation_messages = [
                message.content
                for message in state["messages"]
                if message.type in ("human", "system")
                   or (message.type == "ai" and not message.tool_calls)
            ]

            # Format into prompt
            #docs_content = "\n\n".join(doc.content for doc in tool_messages)
            final_prompt = (
                "As an experienced financial advisor, your task is to analyze economic trends for Apple (AAPL). You are "
                f"required to conduct comprehensive research as requested by the user: {conversation_messages} . Your "
                "analysis should identify key factors. Provide detailed insights and actionable recommendations for "
                "stakeholders. Your report should be clear, concise, and backed by the data provided below:\n\n "
                f"{recent_tool_messages}. Make sure to reference the document when generating an answer.\n Enabling "
                f"informed decision-making for investors and businesses within the sector. If you do not obtain an "
                f"answer from the provided data, reply back that you do not know the answer to the question. Do not lie"
                f".\n\n"
            )

            # NOTE there is a max_token threshold for our Llm (4096).
            prompt = [final_prompt]

            # Run
            response = llm.invoke(prompt)

            return {"messages": [response]}
        except Exception as e:
            print(f"Error {e} retrieving the memory buffer and generating the final message.")

    # Here we are actually building our LangGraph, a diagram that represents how it is built can be seen under the
    # file_outputs folder. The rendering of the graph is done in the main application thread.

    graph = StateGraph(MessagesState) # NOTE: this graph uses the chain of messages to maintain a state.
    graph.add_node(query_or_respond)
    graph.add_node(tools)
    graph.add_node(generate)

    graph.set_entry_point("query_or_respond")
    graph.add_conditional_edges(
        "query_or_respond",
        tools_condition,
        {END: END, "tools": "tools"},
    )
    graph.add_edge("tools", "generate")
    graph.add_edge("generate", END)

    graph = graph.compile()

    return graph