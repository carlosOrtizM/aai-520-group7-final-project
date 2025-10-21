# https://langchain-ai.github.io/langgraph/tutorials/workflows/
from langchain_ollama import ChatOllama
# Schema for structured output
from pydantic import BaseModel, Field
from typing import List, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display

llm = ChatOllama(model="llama3.2:latest")

# Calculate the final amount in an investment account over 5 years given varying annual returns, a fixed annual fee, and a tax rate on the gains.

# Prompt chaining
def graph_basic_workflow(llm):
    try:
        # Graph state
        class State(TypedDict):
            user_query: str
            verification: str
            optimized_query: str
            calculator: str
            total_income: str
            answer: str

        # Nodes

        def verifier(state: State):
            print("verifier - log")
            """First LLM call to verify the query has all the data we need """

            msg = llm.invoke(f"Verify that {state['user_query']} has: a list of annual returns (at least for the past 5 years), "
                             f"fixed costs information, and a tax rate on the gains. Explicitly provide either a Y/N type of answer.")
            return {"verification": msg.content}

        def check_conditions(state: State):
            """Gate function to check if the query has passed"""

            print("check_conditions - log")
            # Simple check - does the joke contain "?" or "!"
            if "Y" in state["verification"] or "y" in state["verification"]:
                return "Pass"
            return "Fail"

        def query_optimizer(state: State):
            """Call to optimize the initial query"""

            print("query_optimizer - log")
            msg = llm.invoke(f"Write a Specific, Clear, query from {state['user_query']} that distinctly delineates the "
                             f"annual returns, fixed costs, and tax rate on the gains.")
            return {"optimized_query": msg.content}

        # Define a tool
        def amount_calculator(returns: Optional[List[int]], annual_fee: int, tax_rate: int, years: int) -> int | str:

            print("amount_calculator - log")
            if years != len(returns):
                return 0
            else:
                for income in returns:
                    amount =  income * (1-tax_rate)

                total_income = -(annual_fee * years) + amount
                return f"{int(total_income)}"

        def tool_calculator(state: State):
            """Generate tool call for retrieval or respond."""
            llm_with_tools = llm.bind_tools([amount_calculator])
            response = llm_with_tools.invoke(state["optimized_query"])
            # MessagesState appends messages to state instead of overwriting
            return {"total_income": [response]}

        def output_call(state: State):
            """Reply back to the user with the extracted data"""

            print("output_call - log")
            print(f"output_call - log - state['total_income']")
            msg = llm.invoke(f"Confidently reply back to the user with the total_income received: {state['total_income']}")
            return {"answer": msg.content}

        # Build workflow
        workflow = StateGraph(State)

        # Add nodes
        workflow.add_node("user_query", verifier)
        workflow.add_node("optimized_query", query_optimizer)
        workflow.add_node("calculator", tool_calculator)
        workflow.add_node("total_income", output_call)

        # Add edges to connect nodes
        workflow.add_edge(START, "user_query")
        workflow.add_conditional_edges(
            "user_query", check_conditions, {"Fail": END, "Pass": "optimized_query"}
        )
        workflow.add_edge("optimized_query", "calculator")
        workflow.add_edge("calculator", "total_income")
        workflow.add_edge("total_income", END)

        # Compile
        chain = workflow.compile()

        # Show workflow
        Image(chain.get_graph().draw_mermaid_png(output_file_path=("/home/alberto/Documents/MSAAI/aai-520-group7-final-project/graph.png")))

        prompt = ("How much did I make if I earned [250k, 231k, 50k, 1M, 550k, 67k] in the last couple of years,"
                  "paying 50k a month on stuff, and taxes are at 23%.")
        state = chain.invoke({"user_query": f"{prompt}"})

        print(f"Output {state['verification']}")
        print(f"Output {state['optimized_query']}")
        print(f"Output {state['calculator']}")
        print(f"Output {state['total_income']}")
        print(f"Output {state['answer']}")

    except Exception as e:
        print(f"Error {e} when running the prompt chaining graph.")

graph_basic_workflow(llm)