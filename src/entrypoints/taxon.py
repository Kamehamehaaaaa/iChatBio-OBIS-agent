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
Get Taxonomic records fo species based on their scientific name, common name or Taxon AphiaID.
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
            scientificNameUrl, scientificNames = await utils.getScientificName(params.get("commonname"))

            # print(scientificNames)

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
            
            if params.get('annotationsrequested', False):
                url = utils.generate_obis_url("taxon/annotations", params)
            else:
                if params.get('id', '') != '':
                    url = utils.generate_obis_extension_url("taxon", params, "id", False)
                elif params.get('scientificname', '') != '':
                    url = utils.generate_obis_extension_url("taxon", params, "scientificname", False)
                else:
                    utils.exceptionHandler(process, None, "incorrect params generated")
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
