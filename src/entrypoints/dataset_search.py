from ichatbio.types import AgentEntrypoint
import utils

from instructor.core import InstructorRetryException

from schema import datasetSearchApi

import requests
import http

from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess
from ichatbio.types import AgentEntrypoint

from utils import search_helper as search
from utils import utils

entrypoint= AgentEntrypoint(
    id="dataset_search",
    description="If user needs list of datasets to be fetched by contributor name or author or dataset name.",
    parameters=None
)

async def run(request: str, context: ResponseContext):

    # Start a process to log the agent's actions
    async with context.begin_process(summary="Searching Ocean Biodiversity Information System") as process:
        process: IChatBioAgentProcess

        await process.log("Original request: " + request)

        await process.log("Generating search parameters for dataset search with common terms")
        
        try:
            llmResponse = await search._generate_search_parameters(request, entrypoint, datasetSearchApi)
            if 'clarification_needed' in llmResponse.keys() and llmResponse['clarification_needed']:
                raise Exception(llmResponse['reason'])
            params = llmResponse['params']
        except Exception as e:
            await utils.exceptionHandler(process, e, "Error generating params. ")
            return
        
        await process.log("Generated search parameters", data=params)

        await process.log("Querying OBIS")
        try:

            # datasetFetchUrl, datasets = await utils.getDatasetId(params.get("queryContent"))

            # if not datasets or len(datasets) == 0:
            #     await utils.exceptionHandler(process, None, "The query deosn't satisfy any datasets in OBIS")
            #     return
            
            # await process.create_artifact(
            #     mimetype="application/json",
            #     description="Datasets for the given query",
            #     uris=[datasetFetchUrl],
            #     metadata={
            #         "data_source": "OBIS",
            #         "portal_url": "portal_url",
            #     }, 
            # )
            # return
            
            url = utils.generate_obis_url("dataset/search2", params)
            await process.log(f"Sending a GET request to the OBIS dataset API at {url}")

            response = requests.get(url)
            code = f"{response.status_code} {http.client.responses.get(response.status_code, '')}"

            if response.ok:
                await process.log(f"Response code: {code}")
            else:
                await process.log(f"Response code: {code} - something went wrong!")
                return
            
            try:
                response_json = response.json()
            except ValueError as e:
                await utils.exceptionHandler(process, e, "Failed to decode OBIS response as JSON.")
                return
            
            matching_count = response_json.get("total", 0)
            record_count = len(response_json.get("results", []))


            await process.log(
                text=f"The API query using URL {url} returned {record_count} out of {matching_count} matching records in OBIS"
            )

            await process.create_artifact(
                mimetype="application/json",
                description="OBIS data returned for: "+ params['q'],
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
