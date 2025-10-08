# https://python.langchain.com/docs/tutorials/qa_chat_history/

from langgraph.graph import MessagesState, StateGraph
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import END
from langgraph.prebuilt import ToolNode, tools_condition


# So, this is a function that when executed (executed on the appz.py) it instantiates a langgraph as
# defined by this function

# The langgraph seems to be composed of an input, tools, and an output

def graph_builder(vector_store, llm):
    # graph as a workflow

    # we initialize our langgraph
    graph_builder = StateGraph(MessagesState)

    # tools are things the llm can do/has access to
    # the llm does not actually go and search the VectorDB, it merely decides it wants to use the tool
    # the tool is then activated (and the function defined for the tool is exectuted).

    # there are a lot of predefined tools already https://python.langchain.com/docs/integrations/tools/
    # some even work for our particular use case, we just need to give our model access to them
    # (Google finance) https://python.langchain.com/docs/integrations/tools/google_finance/
    # (Yahoo finance) https://python.langchain.com/docs/integrations/tools/yahoo_finance_news/

    @tool(response_format="content_and_artifact")
    def retrieve(query: str):
        """Retrieve information related to a query."""
        retrieved_docs = vector_store.similarity_search(query, k=3)
        print(retrieved_docs)
        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\nContent: {doc.page_content}")
            for doc in retrieved_docs
        )
        return serialized, retrieved_docs

    # Define a couple of other tools

    # So the graph is executed, at the beginning of the graph it receives an input message (prompt). This step takes
    # place before we enter the graph, and we could introduce a system prompt alongside the user prompt. E.g. you are
    # an expert financial advisor blah blah + the {actual prompt}. Note: this initial system prompt would work to better
    # improve the tool usage, not necessarily the final generative output (another system prompt would go there).

    # With that prompt then the Llm has a collection of tools it can use, or else it can return an output and use
    # no tools.

    # Step 1: Generate an AIMessage that may include a tool-call to be sent.
    def query_or_respond(state: MessagesState):
        """Generate tool call for retrieval or respond."""
        llm_with_tools = llm.bind_tools([retrieve])
        response = llm_with_tools.invoke(state["messages"])
        # MessagesState appends messages to state instead of overwriting
        return {"messages": [response]}


    # If it decides to use the tool, in this case the function that is going to the vectorDB then it executes the
    # function.
    # Step 2: Execute the retrieval.
    tools = ToolNode([retrieve])

    # after it has the new variables returned from the tools + the prompt it already had it moves on to the next node

    # Step 3: Generate a response using the retrieved content.
    def generate(state: MessagesState):
        """Generate answer."""
        # Get generated ToolMessages
        recent_tool_messages = []
        for message in reversed(state["messages"]):
            if message.type == "tool":
                recent_tool_messages.append(message)
            else:
                break
        tool_messages = recent_tool_messages[::-1]

        # Format into prompt
        docs_content = "\n\n".join(doc.content for doc in tool_messages)
        system_message_content = (
            "You are a digital bookkeeper for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. Use three paragraphs maximum and keep the "
            "answer concise."
            "\n\n"
            f"{docs_content}"
        )
        conversation_messages = [
            message
            for message in state["messages"]
            if message.type in ("human", "system")
               or (message.type == "ai" and not message.tool_calls)
        ]
        prompt = [SystemMessage(system_message_content)] + conversation_messages

        # Run the final generative prompt, with all the context provided by the prompts and the tools.
        response = llm.invoke(prompt)
        return {"messages": [response]}

    # here we are actually building the nodes of the langgraph, as previously we were only setting up the defining
    # functions (), here we are telling the node what it actually is made of
    graph_builder.add_node(query_or_respond)
    graph_builder.add_node(tools)
    graph_builder.add_node(generate)

    # here we are setting up the relationships between the nodes, as well as the route they are supposed to take
    graph_builder.set_entry_point("query_or_respond")
    graph_builder.add_conditional_edges(
        "query_or_respond",
        tools_condition,
        {END: END, "tools": "tools"},
    )
    graph_builder.add_edge("tools", "generate")
    graph_builder.add_edge("generate", END)

    # we compile the node and return it (as this was all a defining function () to be instantiated somewhere else.
    graph = graph_builder.compile()

    return graph

# langgraph is then a way to create workflows by means of graphs, where we give an llm access to sets of tools()
# hoping it decides which tools to use in order to provide an accurate answer for the prompt.
# it does not actually go into the DB (for example), rather just executes the function (tool) that goes to the db to do
# something.

# langchain is another library that comes into play. the tools and messages definition, that are used ny the graph is
# done by langchain. if we want to import pre-made tools into our graph, or set up/access Llm (AI), Human, or system
# generated messages this is done by means of langchain. it does not only do this but also provides the other modules
# necessary for successful Agentic projects. Data loaders, partitioners, embedders, tokenizers model clients, db clients
# ... these are all langchain components. I say components because langchain is not actually doing all of that, but is
# rather just the middleware that allows it all to come together in a homogenized library.

# For example when it comes to dataloaders, langchain didn't actually develop (in most cases) the functions that allow
# us to extract structured information from unstructured data types (.pdfs). It is merely middleware that provides
# access to those libraries (unstructured, pdfminer, pdfplumber) and the expected output is turned into Langchain
# objects (standardizing the outputs that this different libararies might've outputed).

# nothing is stopping us from going an using those libraries ourselves, but langchain allows us to only have to learn
# a specific ecosystem (langchain functions/methods, which are afterwards going out and contacting those specific
# libraries.

# this modularity is facilitated by the Library as a Service phenomena going on (API calls). Pay for access to a product
# or service, and by providing your API key, you just have to call on an API, send the info, and they send back whatever
# it is you were asking for in the first place.

# langchain could then be seen as an API wrapper (in most cases). You instantiate a langchain method
# (e.g. RecursiveCharacterTextSplitter, gpt-4 client/call) and if this service is provided by a vendor, it just send
# your API call for you and transforms it to a langchain-specific object.

# there are (thankfully) still some self-hosted options for those who want it. Where you still use the langchain objects
# as middleware, but the libraries/services are downloaded and run in your own computer. You could go and run the
# program/functions yourself (without langchain), but it does provide some convenience having a standardized framework
# if you want to create Agents/Chains. Still, nothing stops you from running the libraries and feeding the results to
# langchain (still using the framework).