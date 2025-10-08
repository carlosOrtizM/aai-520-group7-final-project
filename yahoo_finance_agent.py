# https://python.langchain.com/docs/integrations/tools/yahoo_finance_news/

from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
from langgraph.prebuilt import create_react_agent

# having previously read the agent_creator.py discussion we can see how this is a barebones langchain application were
# we give an llm access to a tool, give it an input prompt, an expect an output. no preprocessing, no langgraph
# (more complicated patterns), just an llm that has the ability to use a tool and with the prompt + output of the tool
# it must generate a response. In this case the tool is going out and placing http (https) requests to the YahooFinance
# API (with a specific stock/query in mind), and parsing the response JSON for the Llm to use it.

# Something worth noting is the tendency for these Generative models to hallucinate, or the possibility of
# corrupted/incorrectly formatted data coming in throught the tools; as well as the multiple different templates the
# data is coming in by means of the different tools. This flexibility of inputs (API grab-n-go) is kept in check
# (in Python) by "Base Models" that standardize inputs and outputs. Be it Langchain (e.g. Langchain documents, Langchain
# AIMessagess..) or library-specific objects (e.g Unstructured objects) most of the times these base models all come
# from a common ancestor: Pydantic models. It is the python library to set up Objects (OOP - Classes).

# This is worth mentioning because we can set up structure in our prompts and expected outputs by means of pydantic as
# well. The highly unreliable "use 3 sentences maximum", or hallucinated "example@@gmail.co@m can be kept in check by
# means of custom pydantic models.

tools = [YahooFinanceNewsTool()]
agent = create_react_agent("ollama:gpt-4.1-mini", tools)

input_message = {
    "role": "user",
    "content": "What happened today with Microsoft stocks?",
}

for step in agent.stream(
    {"messages": [input_message]},
    stream_mode="values",
):
    step["messages"][-1].pretty_print()