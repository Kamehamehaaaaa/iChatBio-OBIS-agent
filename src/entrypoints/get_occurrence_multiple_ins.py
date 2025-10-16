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

import json

description = """
Retrieve occurrence records of species from OBIS matching query criteria. 
When query asks for species records and not just summary or total number of records direct them here.

Here are some examples:
- Get n records of a species from a area or place or region.
- Get records of a species from an institute or dataset.
- Records found in a geographic location during a period.
"""

entrypoint= AgentEntrypoint(
    id="get_occurrence_2",
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
            if 'clarification_needed' in llmResponse.keys() and llmResponse['clarification_needed']:
                raise Exception(llmResponse['reason'])
            params = llmResponse['params']
        except Exception as e:
            await utils.exceptionHandler(process, e, "Error generating obis parameters.")
            return

        await process.log("Initial params generated", data=params)

        if "area" in params:
            matches = await utils.getAreaId(params.get("area"))
            print("area matches")
            print(matches)
            if len(matches) == 0:
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

        institutes = []

        if "institute" in params:
            institutes = await utils.getInstituteId(params)
            # print(institutes)
            # if matches and len(matches) > 1:
            #     await process.log("Multiple institute matches found")
            # params["instituteid"] = match.get("id")
            del params["institute"]

        
        await process.log("Generated search parameters", data=params)

        await process.log("Querying OBIS")
        try:

            urls = []
            matching_count = 0
            record_count = 0
            institutes_list = ""

            if len(institutes) > 0:
                records = {"total":0, "records": {}}

                for institute in institutes:
                    params["instituteid"] = institute.get("id")
                    institutes_list += institute["name"] + ","
                
                    url = utils.generate_obis_url("occurrence", params)
                    urls.append(url)
                    await process.log(f"Sending a GET request to the OBIS occurrence API at {url}")

                    response = requests.get(url)
                    code = f"{response.status_code} {http.client.responses.get(response.status_code, '')}"

                    if response.ok:
                        await process.log(f"Response code: {code}")
                    else:
                        await process.log(f"Response code: {code} - something went wrong!")
                        return
                    
                    response_json = response.json()

                    records["records"][institute.get("name")] = response_json.get("results", [])
                
                    matching_count += response_json.get("total", 0)
                    record_count += len(response_json.get("results", []))

                records["total"] = matching_count

                await process.log(
                    text=f"The API query returned {record_count} out of {matching_count} matching records in OBIS"
                )

                # print(records)

                content = json.dumps(records).encode("utf-8")
                artifact_description = "OBIS has " + str(len(institutes)) + " matching with the query input of institute name. " + \
                                        "They are " + institutes_list + "Retrieve 10 records for each of them."

            else:
                url = utils.generate_obis_url("occurrence", params)
                urls.append(url)

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
            print(e)
            await process.log("Sorry, I couldn't find any species occurrences.")
