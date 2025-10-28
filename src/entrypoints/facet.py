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
            params = await search._generate_search_parameters(request, entrypoint, facetsAPIParams)
        except Exception as e:
            await process.log("Error generating params.")

            return
        
        params = params["params"]
        
        if "area" in params or ("areaid" in params and type(params["areaid"]) != int):
            matches = await utils.getAreaId(params.get("areaid"))
            print(matches)
            if len(matches) > 1:
                await process.log("Multiple area matches found")
            params["areaid"] = matches[0].get("areaid")
            if "area" in params:
                del params["area"]

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
