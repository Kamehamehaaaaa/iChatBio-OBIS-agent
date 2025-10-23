from ichatbio.types import AgentEntrypoint
import utils

from instructor.core import InstructorRetryException

from schema import datasetApi

import requests
import http

from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess
from ichatbio.types import AgentEntrypoint

from utils import search_helper as search
from utils import utils

entrypoint= AgentEntrypoint(
    id="dataset",
    description="Get dataset records from OBIS. Queries like 'get datasets which have records of brachyura' is resolved here.",
    parameters=None
)

async def run(request: str, context: ResponseContext):

    # Start a process to log the agent's actions
    async with context.begin_process(summary="Searching Ocean Biodiversity Information System") as process:
        process: IChatBioAgentProcess

        await process.log("Original request: " + request)

        await process.log("Generating search parameters for dataset records")
        
        try:
            llmResponse = await search._generate_search_parameters(request, entrypoint, datasetApi)
            if 'clarification_needed' in llmResponse.keys() and llmResponse['clarification_needed']:
                raise Exception(llmResponse['reason'])
            params = llmResponse['params']
        except Exception as e:
            print(e)
            await process.log("Error generating params. " + e)

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
            params["instituteid"] = matches[0].get("id")
            del params["institute"]

        
        await process.log("Generated search parameters", data=params)

        await process.log("Querying OBIS")
        try:
            
            url = utils.generate_obis_url("dataset", params)
            await process.log(f"Sending a GET request to the OBIS dataset API at {url}")

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
            await process.log("Sorry, I couldn't find any species datasets.")
