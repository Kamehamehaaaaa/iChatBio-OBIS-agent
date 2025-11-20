# import langgraph as lg
# from langgraph import Node, Edge, Graph

# # Example function to simulate querying an endpoint
# def query_endpoint(endpoint, params):
#     # Simulate an API call to the endpoint
#     print(f"Querying {endpoint} with params: {params}")
#     # Simulated response
#     return {"status": "success", "data": "Some result from the API"}

# # Define the function that generates API parameters
# def generate_api_params(user_request):
#     # Based on the user request, dynamically generate params
#     return {"query": user_request}

# # Define logic to choose the next endpoint based on the request or response
# def choose_next_endpoint(user_request, previous_response):
#     if previous_response["status"] == "success":
#         # If previous response was good, we can stop
#         return None
#     else:
#         # Otherwise, choose another endpoint
#         return "endpoint2"  # For example

# # Define LangGraph nodes
# class StartNode(Node):
#     def run(self, user_request):
#         # Generate initial params from user input
#         params = generate_api_params(user_request)
#         print(f"Initial Params: {params}")
#         return params, "endpoint1"  # Start with the first endpoint

# class QueryNode(Node):
#     def run(self, params, endpoint):
#         # Query the selected endpoint
#         response = query_endpoint(endpoint, params)
#         print(f"Response from {endpoint}: {response}")
#         return response

# class DecisionNode(Node):
#     def run(self, response, user_request):
#         # Decide if we need to query more endpoints based on the response
#         next_endpoint = choose_next_endpoint(user_request, response)
#         if next_endpoint:
#             # Continue querying another endpoint
#             return True, next_endpoint
#         else:
#             # End the pipeline if the response is valid
#             return False, response["data"]

# # Create the LangGraph pipeline
# graph = Graph()

# # Define the workflow by chaining the nodes
# start = StartNode("StartNode")
# query = QueryNode("QueryNode")
# decision = DecisionNode("DecisionNode")

# # Connect the nodes
# graph.add_edge(Edge(start, query, params="user_request"))
# graph.add_edge(Edge(query, decision, response="response"))
# graph.add_edge(Edge(decision, query, next_endpoint="next_endpoint"))
# graph.add_edge(Edge(decision, None, final_response="data"))

# # Run the pipeline with a user request
# user_request = "Get weather data"
# final_response = graph.run(user_request)

# print(f"Final Response: {final_response}")


from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator
from langchain_openai import ChatOpenAI
from utils import utils
from agent import OBISAgent
from ichatbio.agent_response import ResponseContext, ResponseMessage, ResponseChannel

import time

from schema import AnalyzeRequestResponse

from entrypoints import get_occurrence, taxon, institute, dataset, facet, checklist, dataset_lookup, institute_lookup

# Define the state structure
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_request: str
    endpoints_called: list[str]
    accumulated_data: dict
    is_complete: bool
    next_endpoint: str | None
    context: ResponseContext | None

# Node functions
async def analyze_request(state: AgentState) -> AgentState:
    """
    Analyze user request and determine which endpoint to call first.
    Uses LLM to understand intent and select appropriate endpoint.
    """
    user_request = state["user_request"]
    
    # Use your LLM here to analyze request and select endpoint
    # Example prompt:
    prompt = f"""
    Given this user request: "{user_request}"
    
    Available endpoints:
    1. {get_occurrence.entrypoint.id} - {get_occurrence.entrypoint.description}
    2. {taxon.entrypoint.id} - {taxon.entrypoint.description}
    3. {institute.entrypoint.id} - {institute.entrypoint.description}
    4. {dataset.entrypoint.id} - {dataset.entrypoint.description}
    5. {facet.entrypoint.id} - {facet.entrypoint.description}
    6. {dataset_lookup.entrypoint.id} - {dataset_lookup.entrypoint.description}
    7. {institute_lookup.entrypoint.id} - {institute_lookup.entrypoint.description}
    8. {checklist.entrypoint.id} - {checklist.entrypoint.description}
    
    Which endpoint should be called first?. Make a sound choice. Do not assume or make up your own calls. Chose from the given set of entrypoints. Return all the entrypoints that you think are required.
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=utils.getValue("OPEN_API_KEY"), base_url=utils.getValue("OPENAI_BASE_URL"))
    structured_llm = llm.with_structured_output(schema=AnalyzeRequestResponse)
    # chain = prompt | llm 
    
    # try:
    #     plan = await chain.ainvoke({
    #         "format_instructions": parser.get_format_instructions(),
    #         "request": user_request,
    #         "species": species_names if species_names else "unknown"
    #     })
        
    #     return ResearchPlan(**plan)
    
    # except Exception as e:
    #     # Fallback plan if LLM fails
    #     #print(f"Warning: Plan creation failed ({e}), using fallback plan")

    llm_response = structured_llm.invoke(prompt)
    print("rohit:\n", user_request, llm_response)
    # For demo, let's assume it returns "users_endpoint"
    next_endpoint = llm_response.entrypoints.pop(0)  # Replace with actual LLM call
    print("after entrypoint extraction" ,llm_response)
    
    return {
        **state,
        "next_endpoint": next_endpoint,
        "messages": state["messages"] + [AIMessage(content=f"Starting with {next_endpoint}")]
    }

async def call_endpoint(state: AgentState) -> AgentState:
    """
    Call the selected endpoint with LLM-generated parameters.
    """
    print("rohit:" , state)
    # time.sleep(10)
    endpoint_name = state["next_endpoint"]
    user_request = state["user_request"]
    accumulated_data = state["accumulated_data"]
    
    # Call your actual endpoint
    agent = OBISAgent()  
    endpoint_response = await agent.run(state["context"], user_request, endpoint_name, None)
    endpoint_response = {"data": f"Response from {endpoint_name}"}

    print("ROhit endpoint called")
    # time.sleep(10)
    
    # Update state
    new_accumulated_data = {**accumulated_data, endpoint_name: endpoint_response}
    new_endpoints_called = state["endpoints_called"] + [endpoint_name]
    
    return {
        **state,
        "accumulated_data": new_accumulated_data,
        "endpoints_called": new_endpoints_called,
        "messages": state["messages"] + [AIMessage(content=f"Called {endpoint_name}")]
    }

async def check_completion(state: AgentState) -> AgentState:
    """
    Use LLM to determine if we have enough data to answer the user's request.
    """
    # user_request = state["user_request"]
    accumulated_data = state["accumulated_data"]
    endpoints_called = state["endpoints_called"]
    
    # # Use LLM to determine if request is satisfied
    # prompt = f"""
    # User request: "{user_request}"
    # Data collected so far: {accumulated_data}
    # Endpoints called: {endpoints_called}
    
    # Questions:
    # 1. Is this enough data to fully answer the user's request? (yes/no)
    # 2. If no, which endpoint should be called next?
    
    # Respond in JSON format:
    # {{
    #     "is_complete": true/false,
    #     "next_endpoint": "endpoint_name" or null,
    #     "reasoning": "explanation"
    # }}
    # """

    # llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=utils.getValue("OPEN_API_KEY"), base_url=utils.getValue("OPENAI_BASE_URL"))
    
    # llm_response = llm.invoke(prompt)

    # print("check completion:\n", llm_response)
    
    return {
        **state,
        "is_complete": True if endpoints_called[-1] in accumulated_data.keys() else False,
        "next_endpoint": "nothing",
        "messages": state["messages"] + ["Just check for entrypoint output"]
    }

def generate_response(state: AgentState) -> AgentState:
    """
    Generate final response to user based on all collected data.
    """
    user_request = state["user_request"]
    accumulated_data = state["accumulated_data"]
    
    # Use LLM to synthesize final answer
    prompt = f"""
    User request: "{user_request}"
    Collected data: {accumulated_data}
    
    Generate a comprehensive response to the user's request.
    """
    
    # final_response = llm.invoke(prompt)
    final_response = f"Based on data from {len(accumulated_data)} endpoints, here's your answer..."
    
    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=final_response)]
    }

# Routing function
def should_continue(state: AgentState) -> str:
    """
    Determine whether to continue calling endpoints or finish.
    """
    if state["is_complete"]:
        return "success"
    else:
        return "call_endpoint"

def time_condition(state):
    start = state["start_time"]
    if time.time() - start > 20:
        return 'abort'
    return 'success'
    
# Build the graph
def create_workflow():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("analyze_request", analyze_request)
    workflow.add_node("call_endpoint", call_endpoint)
    workflow.add_node("check_completion", check_completion)
    # workflow.add_node("generate_response", generate_response)
    
    # Add edges
    workflow.set_entry_point("analyze_request")
    workflow.add_edge("analyze_request", "call_endpoint")

    # workflow.add_conditional_edges(
    #     "call_endpoint",
    #     time_condition,
    #     {
    #         "abort": "abort",
    #         "success": "check_completion"
    #     }
    # )

    workflow.add_edge("call_endpoint", "check_completion")
    
    # Conditional edge based on completion status
    workflow.add_conditional_edges(
        "check_completion",
        should_continue,
        {
            "call_endpoint": "call_endpoint",
            "success": END
        }
    )
    
    # workflow.add_edge("generate_response", END)
    # workflow.add_edge('check_completion', END)
    
    return workflow.compile()

# Usage example
async def run_pipeline(context, user_request: str):
    app = create_workflow()
    
    initial_state = {
        "messages": [HumanMessage(content=user_request)],
        "user_request": user_request,
        "endpoints_called": [],
        "accumulated_data": {},
        "is_complete": False,
        "next_endpoint": None,
        "context": context
    }
    
    # Run the graph
    result = await app.ainvoke(initial_state)
    
    return result

from ichatbio.agent import IChatBioAgent
from ichatbio.types import AgentCard
from ichatbio.server import run_agent_server
from typing import Optional

from pydantic import BaseModel
from ichatbio.types import AgentEntrypoint

class OBISGraph(IChatBioAgent):
    def __init__(self):
        super().__init__()
        self.entrypoint = AgentEntrypoint(id="entrypoint1", description="trial", parameters=None)

    def get_agent_card(self) -> AgentCard:
        return AgentCard(
            name="Ocean Biodiversity Information Systems data source",
            description="Retrieves data from OBIS (https://api.obis.org).",
            icon=None,
            entrypoints=[
                self.entrypoint
                ]
        )

    async def run(self, context: ResponseContext, request: str, entrypoint: str, params: Optional[BaseModel]):
        await run_pipeline(context, user_request=request)
        await context.reply("OBIS query completed")

# Example usage
if __name__ == "__main__":
    # import asyncio
    # result = asyncio.run(run_pipeline("occurrences of great white shark"))
    # print("Final state:", result)
    # print("\nMessages:")
    # for msg in result["messages"]:
    #     print(f"  {msg.content}")

    # print(result["accumulated_data"])
    agent = OBISGraph()
    run_agent_server(agent, "localhost", 8990)
    