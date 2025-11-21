from ichatbio.types import AgentEntrypoint
# from ichatbio.types import Message, TextMessage, ProcessMessage, ArtifactMessage
import utils
from openai import OpenAI, AsyncOpenAI

import instructor
from instructor.core import InstructorRetryException

from schema import occurrenceApi
from tenacity import AsyncRetrying

import requests
import http

from ichatbio.agent import IChatBioAgent
from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess
from ichatbio.types import AgentCard, AgentEntrypoint

from utils import search_helper as search
from utils import utils

# from langchain.agents import tool
# from artifact_registry import ArtifactRegistry

description = """
Retrieve occurrence records of species from OBIS matching query criteria. Also retrives an individual occurrence record.
When query asks for species records and not just summary or total number of records direct them here.

Here are some examples:
- Get n records of a species from a area or place or region.
- Get records of a species from an institute or dataset.
- Records found in a geographic location during a period.
- Get occurrence record with id 0000039c-74cd-4e37-9bf8-848d560bf519
"""

entrypoint= AgentEntrypoint(
    id="get_occurrence",
    description=description,
    parameters=None
)

async def run(request: str, context: ResponseContext):

    # Start a process to log the agent's actions
    async with context.begin_process(summary="Searching Ocean Biodiversity Information System") as process:
        process: IChatBioAgentProcess

        await process.log("Original request: " + request)

        await process.log("Generating search parameters for species occurrences")
        
        try:
            llmResponse = await search._generate_search_parameters(request, entrypoint, occurrenceApi)
            
            if not llmResponse or "params" not in llmResponse:
                exception = "Search parameters could not be generated from request."
                if 'reason' in llmResponse:
                    exception += llmResponse['reason']
                raise Exception(exception)
            params = llmResponse['params']
            if 'clarification_needed' in llmResponse.keys() and llmResponse['clarification_needed']:
                exception = 1
                if unresolved := llmResponse.get('unresolved_params', ''):
                    if 'institute' in params and 'instituteid' in unresolved:
                        exception = 0
                if exception:
                    raise Exception(llmResponse['reason'])
        except Exception as e:
            await utils.exceptionHandler(process, e, "Error generating obis parameters.")
            return

        await process.log("Initial params generated", data=params)

        # when area and institute in request institute gets higher priority

        if "institute" in params:
            if not await utils.resolveParams(params, "institute", "instituteid", process):
                return

        if "area" in params:
            if not await utils.resolveParams(params, "area", "areaid", process):
                return

        if "datasetname" in params:
            if not await utils.resolveParams(params, "datasetname", 'datasetid', process):
                return
            
        if "commonname" in params:
            if not await utils.resolveParams(params, "commonname", "taxonid", process):
                return 

        
        await process.log("Generated search parameters", data=params)

        await process.log("Querying OBIS")
        try:

            urls = []

            if "id" in params:
                url = utils.generate_obis_extension_url("occurrence/", params, "id", False)
            else:
                url = utils.generate_obis_url("occurrence", params)
            urls.append(url)

            await process.log(f"Sending a GET request to the OBIS occurrence API at {url}")

            try:
                response = requests.get(url, timeout=10)
            except requests.exceptions.RequestException as e:
                await process.log(f"Failed to connect to OBIS API: {e}")
                await utils.exceptionHandler(process, e, "Failed to Connect to OBIS")
                return
            
            code = f"{response.status_code} {http.client.responses.get(response.status_code, '')}"

            if response.ok:
                await process.log(f"OBIS data retrived successfully: {code}")
            else:
                await process.log(f"OBIS returned error {response.status_code} - something went wrong!")
                return
            
            try:
                response_json = response.json()
            except ValueError as e:
                await process.log("Failed to decode OBIS response as JSON.")
                await utils.exceptionHandler(process, e, "Failed to decode OBIS response as JSON.")
                return

        
            matching_count = response_json.get("total", 0)
            record_count = len(response_json.get("results", []))

            await process.log(
                text=f"The API query returned {record_count} out of {matching_count} matching records in OBIS"
            )

            content = None
            artifact_description = "Occurrence records from OBIS"

            await process.create_artifact(
                mimetype="application/json",
                description=artifact_description,
                uris=urls,
                metadata={
                    "data_source": "OBIS",
                    "portal_url": "portal_url",
                    "retrieved_record_count": record_count,
                    "total_matching_count": matching_count
                }, 
                content=content,
            )

        except InstructorRetryException as e:
            await process.log("Sorry, information retrival failed.")
