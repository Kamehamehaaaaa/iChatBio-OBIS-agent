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
Retrieve occurrence records of species from OBIS matching query criteria. 
When query asks for species records and not just summary or total number of records direct them here.

Here are some examples:
- Get n records of a species from a area or place or region.
- Get records of a species from an institute or dataset.
- Records found in a geographic location during a period.
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

        # when area and institute in request institute gets higher priority"

        institutes = []

        if "institute" in params:
            institutes = await utils.getInstituteId(params)
            if not institutes or len(institutes) == 0:
                await process.log("OBIS doesn't have any institutes named " + params["institute"])
                return
            
            if institutes[0].get("score") < 0.80:
                institute = ""+institutes[0].get("name", "")
                if len(institutes) > 1:
                    for i in institutes[1:]:
                        institute += ", " + i.get("name", "")
                    ret_log = "OBIS has " + str(len(institutes)) + " closest matching institute names with the input. " + \
                                            "They are " + institute + ". Records for " + institutes[0].get("name", "") + \
                                            " will be fetched"
                    await process.log(ret_log)
            params["instituteid"] = institutes[0].get("id", "")
            del params["institute"]
            if "area" in params:
                del params["area"]

        if "area" in params:
            matches = await utils.getAreaId(params.get("area"))
            # print("area matches")
            # print(matches)
            if not matches or len(matches) == 0:
                await utils.exceptionHandler(process, None, "The area specified doesn't match any OBIS list of areas")
                return
            if len(matches) > 1:
                await process.log("Multiple area matches found")
            areas = ""+matches[0].get("areaid")
            for match in matches[1:]:
                areas+=","
                areas+=match.get("areaid")
            params["areaid"] = areas
            del params["area"]

        if "datasetname" in params:
            datasetFetchUrl, datasets = await utils.getDatasetId(params.get("datasetname"))

            if not datasets or len(datasets) == 0:
                await utils.exceptionHandler(process, None, "The dataset specified doesn't match any OBIS list of datasets")
                return
            
            if len(datasets) == 1:
                params['datasetid'] = datasets[0][0]
                del params['datasetname']
            elif len(datasets) > 1:
                utils.exceptionHandler(process, None, "Multiple datasets found for the given query")
                content = "Multiple datasets matches found: " + datasets[0][1]
                for i in datasets[1:]:
                    content += ", "
                    content += i[1]
                await process.create_artifact(
                    mimetype="application/json",
                    description="multiple dataset matches found for the given query",
                    uris=[datasetFetchUrl],
                    metadata={
                        "data_source": "OBIS",
                        "portal_url": "portal_url",
                    }, 
                    content=content
                )
                return
            
        if "commonname" in params:
            scientificNameUrl, scientificNames = await utils.getScientificName(params.get("commonname"))

            if scientificNames == None or len(scientificNames) == 0:
                await utils.exceptionHandler(process, None, f"No scientific names found for {params.get("commonname")}")
                return
            
            if len(scientificNames) == 1:
                params['scientificname'] = scientificNames[0][1]
                del params['commonname']
            elif len(scientificNames) > 1:
                # await utils.exceptionHandler(process, None, "Multiple scientific names found for the given species")
                content = "Multiple scientific name matches found : \n " + scientificNames[0][0] + " -> " +scientificNames[0][1]
                for i in scientificNames[1:(min(5, len(scientificNames)))]:
                    content += "\n"
                    content += i[0] + " -> " + i[1]
                content += "\n"
                content += f"Fetching records for {scientificNames[0][1]}"
                
                await process.log(content)
                params['scientificname'] = scientificNames[0][1]
                del params['commonname']

        
        await process.log("Generated search parameters", data=params)

        await process.log("Querying OBIS")
        try:

            urls = []
            
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
            artifact_description = "OBIS returned the following data for the query: " + request

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
