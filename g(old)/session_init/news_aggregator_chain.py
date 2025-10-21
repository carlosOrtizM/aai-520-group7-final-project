import os
from langgraph.constants import START
from langgraph.graph import StateGraph
from langgraph.graph import END
from session_init.market_news_provider import MarketNewsProvider
from session_init.llm_loader import llm_client_loader
from utilities.core_utils import render_graph
from utilities.metric_utils import basic_logger
from pydantic import Field, BaseModel
from langgraph.graph import MessagesState
from typing import Annotated, Literal
import operator
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import Send
from typing import List, TypedDict

# AAA

@basic_logger
def graph_builder(llm):
    try:
        # Schema for structured output
        #State definitions...
        class News_Analyzer(BaseModel):
            news_article_content: str = Field(description="The news article content to be analyzed.")
            metadata: str = Field(description="The metadata for the specific news article.")

        # messages + structured output
        class FinancialReport(BaseModel):
            news_analysts: List[News_Analyzer] = Field(description="Group of financial articles, each containing both"
                                                                   "information and relevant metadata.")

        # Internal states (dynamic)
        # Augment the LLM with schema for structured output
        planner = llm.with_structured_output(FinancialReport)

        # Internal State definition

        class State(MessagesState):
            news_source: str  # news articles all together
            news_articles: list[News_Analyzer]  # list of news articles divided into metadata and content
            completed_analyses: Annotated[
                list, operator.add
            ]  # Shared key for the analysts to write to
            macro_financial_report: str

        class WorkerState(TypedDict):
            news_article: News_Analyzer
            completed_analyses: Annotated[list, operator.add]  # keys must match with other State!

        # Nodes / Tools
        def orchestrator(state: State):
            try:
                """Orchestrator that splits the collection of news articles into singular news articles, each with corresponding
                 metadata and content.
                """

                # Generate queries...
                news_articles = planner.invoke(
                    [
                        SystemMessage(
                            content="Split the following text into into distinct singular news articles, each with corresponding metadata and content."
                                    "Do not mix news articles together, keep each topic in ints own container/bucket."),
                        HumanMessage(content=f"Assign to each split both the content and corresponding metadata: {state["news_source"]}."),
                    ]
                )

                return {"news_articles": news_articles.news_analysts}

            except Exception as e:
                print(f"Error {e} during the orchestrator process.")

        class News_Summary(BaseModel):
            summary: str = Field(description="The summary of the news article.")
            label: Literal["inflation", "rates", "fed", "macro"] = Field(description="The label for the news article.")

        summarizer = llm.with_structured_output(News_Summary)

        def llm_call(state: WorkerState):
            """Worker writes a summary about the given news article. It also classifies the news article with a
            macroeconomic label.
            """

            try:
                print(f"LLM call instantiated {state['news_article'].metadata}.")

                analysis = summarizer.invoke(
                    [
                        SystemMessage(
                            content="Summarize the following news article in two clear and concise paragraph, capturing the key ideas "
                                    "without missing critical points. Ensure the summary is easy to understand and avoids "
                                    "excessive detail. Be sure to also label the news article accordingly."
                        ),
                        HumanMessage(
                            content=f"Here is the news article: {state['news_article'].news_article_content} with corresponding metadata: "
                                    f"{state['news_article'].metadata}."
                        ),
                    ]
                )

                serialized_summary = "".join(f"{analysis.summary} {analysis.label}")

                print(f"Summary is {serialized_summary}.")

                # Write the final amount that was calculated.
                return {"completed_analyses": [serialized_summary]}

            except Exception as e:
                print(f"Error {e} during the llm-call process.")

        def synthesizer(state: State):
            """Synthesize a summary report from the collection of news articles. Don't forget to include the
            macroeconomic label for each news article."""
            try:
                # List of completed sections
                completed_report = state["completed_analyses"]

                # Format completed section to str to use as context for final sections
                serialized_completed_report = "\n\n---\n\n".join(completed_report)

                return {"macro_financial_report": serialized_completed_report}
            except Exception as e:
                print(f"Error {e} during the synthesizer process.")

        # Conditional edge function to create llm_call workers that each write a section of the report
        def assign_workers(state: State):
            try:
                """Assign a worker to each news article in the collection of news articles."""

                # Kick off section writing in parallel via Send() API
                return [Send("llm_call", {"news_article": s}) for s in state["news_articles"]]
            except Exception as e:
                print(f"Error {e} during the worker assignment process.")

        # Build workflow
        orchestrator_worker_builder = StateGraph(State)

        # Add the nodes
        orchestrator_worker_builder.add_node("orchestrator", orchestrator)
        orchestrator_worker_builder.add_node("llm_call", llm_call)
        orchestrator_worker_builder.add_node("synthesizer", synthesizer)

        # Add edges to connect nodes
        orchestrator_worker_builder.add_edge(START, "orchestrator")
        orchestrator_worker_builder.add_conditional_edges(
            "orchestrator", assign_workers, ["llm_call"]
        )
        orchestrator_worker_builder.add_edge("llm_call", "synthesizer")
        orchestrator_worker_builder.add_edge("synthesizer", END)

        # Compile the workflow
        orchestrator_worker = orchestrator_worker_builder.compile()
        return orchestrator_worker
    except Exception as e:
        print(f"Error {e} during the graph building process.")

# Invoke
llm_client = llm_client_loader()
graph = graph_builder(llm_client)
render_graph(graph)
mn = MarketNewsProvider(category="forex", api_key=os.getenv("FINNHUB_API_KEY"))
market_news = mn.fetch()
state = graph.invoke({"news_source": f"{market_news}"})
print(state["macro_financial_report"])