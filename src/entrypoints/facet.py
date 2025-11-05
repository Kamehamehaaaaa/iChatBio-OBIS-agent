from ichatbio.types import AgentEntrypoint
import utils
from openai import OpenAI, AsyncOpenAI

import instructor
from instructor.core import InstructorRetryException

from schema import facetsAPIParams
from tenacity import AsyncRetrying

import requests
import http

from ichatbio.agent import IChatBioAgent
from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess
from ichatbio.types import AgentCard, AgentEntrypoint

from utils import search_helper as search
from utils import utils

entrypoint= AgentEntrypoint(
    id="facet",
    description="""
        Get record counts for one or more facets from OBIS.
        Use this endpoint when you want to obtain summary counts of occurrence records broken down by one or more attributes (facets) rather than retrieving the full list of records.
        The API allows you to ask: “How many occurrences meet these filters?” and “How many occurrences do we have per value of this facet?” For example, you might ask for counts per year, per taxonomic rank (family or genus), per dataset, per institution, per area, or other relevant facets.
        This is especially useful when you need an overview of data distribution — e.g., to identify hotspots, to check data volume for a particular group, or to decide which subset of data you might confidently query next.
        The Facet API is more efficient than retrieving full occurrence lists when you dont actually need the full data, only counts or distributions.
        Key features
        Returns counts (per facet value) for one or more facet categories.
        Allows you to explore the data at a higher level, e.g., “How many records by year?”, “Which dataset has the most records for my species?”, “Which institution holds the most data for this taxonomic group?”
        When to use:
            When you want to summarize rather than download raw records.
            When you are exploring data coverage, deciding on which subset to retrieve, or doing a high-level check of data availability.
            If the user asking about counts, distributions, or breakdowns
        Limitations
            It does not return the full occurrence records themselves (for that, use the occurrence endpoint).
            The facet breakdown may be limited to certain predefined fields/facets that OBIS supports.
        Example usage
            Get counts of occurrence records for species X by year.
            Get counts of records in area Y by dataset.
            Compare numbers of records across institutions for a given taxonomic group.
    """,
    parameters=None
)


async def run(request: str, context: ResponseContext):

    # Start a process to log the agent's actions
    async with context.begin_process(summary="Searching Ocean Biodiversity Information System") as process:
        process: IChatBioAgentProcess

        await process.log("Generating search parameters for species facet")
        
        try:
            llmResponse = await search._generate_search_parameters(request, entrypoint, facetsAPIParams)
            
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

        await process.log("search parameters", data=params)

        await process.log("Querying OBIS")
        try:
            
            url = utils.generate_obis_url("facet", params)
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
            flag_count = len(response_json.get("results", {}))

            await process.log(
                text=f"The API query using URL {url} returned facets for {flag_count} of flags from OBIS"
            )

            await process.create_artifact(
                mimetype="application/json",
                description="OBIS data for the prompt: " + request,
                uris=[url],
                metadata={
                    "data_source": "OBIS",
                    "portal_url": "portal_url",
                    "retrieved_flag_count": flag_count,
                    "total_matching_count": matching_count
                }
            )

        except InstructorRetryException as e:
            print(e)
            await process.log("Sorry, I couldn't find any species occurrences.")
