from typing import override, Optional, AsyncGenerator, AsyncIterator, override, Iterable

from pydantic import BaseModel

import langchain.agents
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from artifact_registry import ArtifactRegistry

from ichatbio.agent import IChatBioAgent
from ichatbio.types import AgentCard, Artifact
from entrypoints import get_occurrence, facet#, checklist, statistics, get_single_occurrence, statistics_year, facet, institute, species_by_country

from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess

from utils import utils, search_helper as search
import requests

from instructor.exceptions import InstructorRetryException

import http

from schema import occurrenceApi


class OBISAgent(IChatBioAgent):

    def __init__(self):
        super().__init__()

    @override
    def get_agent_card(self) -> AgentCard:
        return AgentCard(
            name="Ocean Biodiversity Information Systems data source",
            description="Retrieves data from OBIS (https://api.obis.org).",
            icon=None,
            entrypoints=[
                get_occurrence.entrypoint,
                # get_single_occurrence.entrypoint,
                # checklist.entrypoint,
                # statistics.entrypoint,
                # statistics_year.entrypoint,
                facet.entrypoint,
                # institute.entrypoint,
                # species_by_country.entrypoint
            ]
        )

    @override
    async def run(self, context: ResponseContext, request: str, entrypoint: str, params: Optional[BaseModel]):

        @tool(return_direct=True)  # This tool ends the agent loop
        async def abort(reason: str):
            """If you can't fulfill the user's request, abort instead and explain why."""
            await context.reply(reason)

        @tool(return_direct=True)  # This tool ends the agent loop
        async def finish(message: str):
            """Mark the user's request as successfully completed."""
            await context.reply(message)

        @tool("get_occurrences")
        async def get_occurrences(request, context):
            # Start a process to log the agent's actions
            async with context.begin_process(summary="Searching Ocean Biodiversity Information System") as process:
                process: IChatBioAgentProcess

                # place_res = await search.get_place_from_request(request)
                # wkt = ""

                # if "place" in place_res:
                #     wkt = await search.place_to_geohash_wkt(place_res["place"], 2)

                await process.log("Generating search parameters for species occurrences")
                
                try:
                    llmResponse = await search._generate_search_parameters(request, entrypoint, occurrenceApi)
                    if 'clarification_needed' in llmResponse.keys() and llmResponse['clarification_needed']:
                        raise Exception(llmResponse['reason'])
                    params = llmResponse['params']
                except Exception as e:
                    print(e)
                    await process.log("Error generating params. ")

                    return

                await process.log("Initial params generated", data=params)
                
                # if "areaid" in params:
                #     del params["areaid"]
                #     await process.log(wkt)
                #     wkt = str(wkt)
                #     wkt_updated = wkt.replace("POLYGON ", "POLYGON")
                #     params["geometry"] = wkt_updated

                if "areaid" in params:
                    matches = await utils.getAreaId(params.get("areaid"))
                    print(matches)
                    if len(matches) > 1:
                        await process.log("Multiple area matches found")
                        return
                    params["areaid"] = matches[0].get("areaid")
                
                await process.log("Generated search parameters", data=params)

                await process.log("Querying OBIS")
                try:
                    
                    url = utils.generate_obis_url("occurrence", params)
                    await process.log(f"Sending a GET request to the OBIS occurrence API at {url}")

                    response = requests.get(url)
                    code = f"{response.status_code} {http.client.responses.get(response.status_code, '')}"

                    if response.ok:
                        await process.log(f"Response code: {code}")
                    else:
                        await process.log(f"Response code: {code} - something went wrong!")
                        return
                    
                    response_json = response.json()
                    
                    matching_count = response_json.get("total", 0)
                    record_count = len(response_json.get("results", []))


                    await process.log(
                        text=f"The API query using URL {url} returned {record_count} out of {matching_count} matching records in OBIS"
                    )

                    await process.create_artifact(
                        mimetype="application/json",
                        description="OBIS data for the prompt: " + request,
                        uris=[url],
                        metadata={
                            "data_source": "OBIS",
                            "portal_url": "portal_url",
                            "retrieved_record_count": record_count,
                            "total_matching_count": matching_count
                        }
                    )

                    await process.log("Querying for point data ")
                    url = utils.generate_obis_url("occurrence/points", params)
                    await process.log(f"Sending a GET request to the OBIS occurrence API at {url}")

                    response = requests.get(url)
                    code = f"{response.status_code} {http.client.responses.get(response.status_code, '')}"

                    if response.ok:
                        await process.log(f"Response code: {code}")
                    else:
                        await process.log(f"Response code: {code} - something went wrong!")
                        return

                    response_json = response.json()

                    record_count = len(response_json.get("coordinates", []))

                    await process.log(
                        text=f"The API query using URL {url} returned {record_count} points matching records in OBIS"
                    )

                    await process.create_artifact(
                        mimetype="application/json",
                        description="OBIS data for the prompt: " + request,
                        uris=[url],
                        metadata={
                            "data_source": "OBIS",
                            "portal_url": "portal_url",
                            "retrieved_record_count": record_count,
                        }
                    )
                    await context.reply(f"I have successfully searched for occurrences and found {record_count} matching records. I've created an artifact with the results.")

                except InstructorRetryException as e:
                    print(e)
                    await process.log("Sorry, I couldn't find any species occurrences.")


        artifacts = ArtifactRegistry(params.artifacts)
        tools = [
            get_occurrences(request, context),
            # facet(request, context),
            abort,
            finish,
        ]

        # Build a LangChain agent graph

        # TODO: make the LLM configurable
        llm = ChatOpenAI(model="gpt-4.1-mini", tool_choice="required")

        system_message = make_system_message(params.artifacts)
        agent = langchain.agents.create_agent(
            model=llm,
            tools=tools,
            prompt=system_message,
        )

        # Run the graph

        await agent.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": request},
                ]
            }
        )

        # match entrypoint:
        #     case get_occurrence.entrypoint.id:
        #         await get_occurrence.run(request, context)
        #     # case get_single_occurrence.entrypoint.id:
        #     #     await get_single_occurrence.run(request, context)
        #     # case checklist.entrypoint.id:
        #     #     await checklist.run(request, context)
        #     # case statistics.entrypoint.id:
        #     #     await statistics.run(request, context)
        #     # case statistics_year.entrypoint.id:
        #     #     await statistics_year.run(request, context)
        #     case facet.entrypoint.id:
        #         await facet.run(request, context)
        #     # case institute.entrypoint.id:
        #     #     await institute.run(request, context)
        #     # case species_by_country.entrypoint.id:
        #     #     await species_by_country.run(request, context)
        #     case _:
        #         raise ValueError()
        await context.reply("OBIS query completed")

SYSTEM_MESSAGE = """
You manipulate structured data using tools. You can access the following artifacts:

{artifacts}

If you are unable to fulfill the user's request using your available tools, abort and explain why.
"""

def list_artifact(artifact: Artifact):
    return f"""\
- local_id: {artifact.local_id}
  description: {artifact.description}
  uris: {artifact.uris}
  metadata: {artifact.metadata}\
"""


def make_system_message(artifacts: Iterable[Artifact]):
    return SYSTEM_MESSAGE.format(
        artifacts=(
            "\n\n".join([list_artifact(artifact) for artifact in artifacts])
            if artifacts
            else "NO AVAILABLE ARTIFACTS"
        )
    ).strip()