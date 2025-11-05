from ichatbio.types import AgentEntrypoint
import utils

from instructor.core import InstructorRetryException

from schema import instituteLookupApi

import requests
import http

from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess
from ichatbio.types import AgentEntrypoint

from utils import search_helper as search
from utils import utils

entrypoint= AgentEntrypoint(
    id="institute_lookup",
    description="Retrieve information about a specific 'institute' from OBIS. Queries like get number of records at an institute are resolved here.",
    parameters=None
)

async def run(request: str, context: ResponseContext):

    # Start a process to log the agent's actions
    async with context.begin_process(summary="Searching Ocean Biodiversity Information System") as process:
        process: IChatBioAgentProcess

        await process.log("Original request: " + request)

        await process.log("Generating search parameters for institute information")
        
        try:
            llmResponse = await search._generate_search_parameters(request, entrypoint, instituteLookupApi)
            if 'clarification_needed' in llmResponse.keys() and llmResponse['clarification_needed']:
                raise Exception(llmResponse['reason'])
            params = llmResponse['params']
        except Exception as e:
            print(e)
            await process.log("Error generating params. " + e)

            return

        await process.log("Initial Params generated", data=params)

        institutes = []

        if "institute" in params:
            institutes = await utils.getInstituteId(params)
            if institutes == None or len(institutes) == 0:
                await process.log("OBIS doesn't have any institutes named " + params["institute"])
                return

            if institutes[0].get("score") < 0.80:
                institute = ""+institutes[0].get("name", "")
                if len(institutes) > 1:
                    for i in institutes:
                        institute += ", " + i.get("name", "")
                    ret_log = "OBIS has " + str(len(institutes)) + " closest matching institute names with the input. " + \
                                            "They are " + institute + ". Information about " + institutes[0].get("name", "") + \
                                            " will be fetched"
                    await process.log(ret_log)
            params["id"] = institutes[0].get("id", "")
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

        await process.log("Params generated", data=params)

        await process.log("Querying OBIS")
        try:
            
            url = utils.generate_obis_extension_url("institute", params, "id", False)
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
