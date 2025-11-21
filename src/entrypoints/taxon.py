from ichatbio.types import AgentEntrypoint
# from ichatbio.types import Message, TextMessage, ProcessMessage, ArtifactMessage
import utils
from openai import OpenAI, AsyncOpenAI

import instructor
from instructor.core import InstructorRetryException

from schema import taxonApi
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
Get Taxonomic records for species based on their scientific name, common name or Taxon AphiaID.
Can also be used to retireve scientific name annotations from WoRMs.
"""

entrypoint= AgentEntrypoint(
    id="taxon",
    description=description,
    parameters=None
)

async def run(request: str, context: ResponseContext):

    # Start a process to log the agent's actions
    async with context.begin_process(summary="Searching Ocean Biodiversity Information System") as process:
        process: IChatBioAgentProcess

        await process.log("Original request: " + request)

        await process.log("Generating search parameters for taxon api")
        
        try:
            llmResponse = await search._generate_search_parameters(request, entrypoint, taxonApi)
            
            if not llmResponse or "params" not in llmResponse:
                exception = "Search parameters could not be generated from request."
                if 'reason' in llmResponse:
                    exception += llmResponse['reason']
                raise Exception(exception)
            params = llmResponse['params']
            if 'clarification_needed' in llmResponse.keys() and llmResponse['clarification_needed']:
                # exception = 1
                # if unresolved := llmResponse.get('unresolved_params', ''):
                #     if 'commonname' in params and 'id' in unresolved:
                #         exception = 0
                # if exception:
                raise Exception(llmResponse['reason'])
        except Exception as e:
            await utils.exceptionHandler(process, e, "Error generating obis parameters.")
            return

        await process.log("Initial params generated", data=params)

        # when area and institute in request institute gets higher priority"
            
        if "commonname" in params:
            if not await utils.resolveParams(params, 'commonname', 'id', process):
                return
            
        if params.get('childtaxonomy', False):
            # we need taxon id for child taxonomy. if scientific name passed resolve it
            if "id" not in params and "scientificname" in params:
                if not await utils.resolveParams(params, 'scientificname', 'id', process):
                    return
     
        await process.log("Generated search parameters", data=params)

        await process.log("Querying OBIS")
        try:

            urls = []
            
            if params.get('annotationsrequested', False):
                url = utils.generate_obis_url("taxon/annotations", params)
            elif params.get('childtaxonomy', False):
                if not params.get('id', False):
                    await utils.exceptionHandler(process, None, "Taxon id missing. Can you please provide taxon id.")
                    return
                url = utils.generate_obis_url(f"taxon/{params.get('id')}/children", None)
            else:
                if params.get('id', '') != '':
                    url = utils.generate_obis_extension_url("taxon", params, "id", False)
                elif params.get('scientificname', '') != '':
                    url = utils.generate_obis_extension_url("taxon", params, "scientificname", False)
                else:
                    await utils.exceptionHandler(process, None, "incorrect params generated")
                    return

                
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
