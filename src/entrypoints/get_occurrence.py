from ichatbio.types import AgentEntrypoint
# from ichatbio.types import Message, TextMessage, ProcessMessage, ArtifactMessage
import utils
from openai import OpenAI, AsyncOpenAI

import instructor
from instructor.exceptions import InstructorRetryException

from schema import occurrenceApi
from tenacity import AsyncRetrying

import requests
import http

from ichatbio.agent import IChatBioAgent
from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess
from ichatbio.types import AgentCard, AgentEntrypoint

from utils import search_helper as search
from utils import utils

from langchain.agents import tool
from artifact_registry import ArtifactRegistry

entrypoint= AgentEntrypoint(
    id="get_occurrence",
    description="Returns occurrence of species from OBIS",
    parameters=None
)

async def run(request: str, context: ResponseContext):

    # Start a process to log the agent's actions
    async with context.begin_process(summary="Searching Ocean Biodiversity Information System") as process:
        process: IChatBioAgentProcess

        await process.log("Original request: " + request)

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

        if "area" in params:
            matches = await utils.getAreaId(params.get("area"))
            print(matches)
            if len(matches) > 1:
                await process.log("Multiple area matches found")
            params["areaid"] = matches[0].get("areaid")
            del params["area"]

        if "institute" in params:
            print("here")
            matches = await utils.getInstituteId(params)
            print(matches)
            # if matches and len(matches) > 1:
            #     await process.log("Multiple institute matches found")
            params["instituteid"] = matches[0].get("id")
            del params["institute"]

        
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

        except InstructorRetryException as e:
            print(e)
            await process.log("Sorry, I couldn't find any species occurrences.")
