from ichatbio.types import AgentEntrypoint
# from ichatbio.types import Message, TextMessage, ProcessMessage, ArtifactMessage
import utils
from openai import OpenAI, AsyncOpenAI

import instructor
from instructor.core import InstructorRetryException

from schema import statisticsApi
from tenacity import AsyncRetrying

import requests
import http

from ichatbio.agent import IChatBioAgent
from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess
from ichatbio.types import AgentCard, AgentEntrypoint

from utils import search_helper as search
from utils import utils

description = """
statistics - Analytical Aggregations

Purpose:
Return structured statistical summaries (aggregated numerical data).

Use when:
User asks for time trends.
User asks for grouped numerical summaries.
Output is intended for reporting or visualization.
Aggregation by year, decade, taxonomic rank, etc.

Examples:
“Year-wise number of occurrences of Egregia menziesii.”
“Trend of records over time.”
“Taxonomic composition across decades.”

Do NOT use for:
Simple categorical counts.
Exploratory dataset/institution breakdowns.
"""

entrypoint= AgentEntrypoint(
    id="statistics",
    description=description,
    parameters=None
)


async def run(request: str, context: ResponseContext):

    # Start a process to log the agent's actions
    async with context.begin_process(summary="Searching Ocean Biodiversity Information System") as process:
        process: IChatBioAgentProcess

        await process.log("Generating search parameters for statistics of species")
        
        try:
            llmResponse = await search._generate_search_parameters(request, entrypoint, statisticsApi)
            
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
            extensions = params.get("statistics_extensions", [])
            if "statistics_extensions" in params:
                del params["statistics_extensions"]
            urls = []
            if len(extensions) == 0:
                urls.append(utils.generate_obis_url("statistics", params))
            for extension in extensions:
                urls.append(utils.generate_obis_url("statistics/"+extension, params))

            for url in urls:
                await process.log(f"Sending a GET request to the OBIS statistics API at {url}")

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
                    await process.log("Failed to decode OBIS response as JSON.")
                    await utils.exceptionHandler(process, e, "Failed to decode OBIS response as JSON.")
                    return

                await process.log(
                    text=f"The API query using URL {url} returned statistics for species from OBIS"
                )

                record_count = len(response_json)

                print("hrer")

                await process.create_artifact(
                    mimetype="application/json",
                    description="OBIS data for the prompt: " + request,
                    uris=[url],
                    metadata={
                        "data_source": "OBIS",
                        "portal_url": "portal_url",
                        "retrieved_record_count": record_count
                    }
                )

                await process.log("artifact created")
        except InstructorRetryException as e:
            print(e)
            await process.log("Sorry, I couldn't find any species statistics.")
