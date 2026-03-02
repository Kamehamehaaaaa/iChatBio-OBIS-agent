from openai import AsyncOpenAI
from utils import prompt_helper as prompt
from utils import utils as utils
import instructor
from ichatbio.types import AgentEntrypoint

import sys

from typing import Type, Optional
from pydantic import BaseModel, Field, create_model
# import requests

async def create_response_model(api_model: Type[BaseModel]) -> Type[BaseModel]:
    response_model = create_model(
                        "response_model",
                        params = (
                            Optional[api_model],
                            Field(
                                description="API parameters extracted from user request",
                                default=None,
                            ),
                        ),
                        unresolved_params = (
                            Optional[list[str]],
                            Field(
                                description="Any parameters that you fail to resolve from user request and need clarification.",
                                default=None,
                            ),
                        ),
                        clarification_needed = (
                            Optional[bool],
                            Field(
                                description="Set to true if you need calrification with any parameters",
                                default=None
                            )
                        ),
                        reason = (
                            Optional[str],
                            Field(
                                description="space for you to provide your reasoning as to why you have populated the params or unresolved_params",
                                default=None
                            )
                        ),
                    )
    
    return response_model

async def _generate_search_parameters(request: str, entrypoint: AgentEntrypoint, returnModel):
    system_prompt = prompt.build_system_prompt(entrypoint.id)

    response_model = await create_response_model(returnModel)
        
    client = AsyncOpenAI(api_key=utils.getValue("OPEN_API_KEY"), base_url=utils.getValue("OPENAI_BASE_URL"))
    
    instructor_client = instructor.patch(client)

    req = await instructor_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=response_model,
        messages=[
            {"role": "system",
                "content": system_prompt},
            {"role": "user", "content": request}],
        temperature=0,
    )

    generation = req.model_dump(exclude_none=True, by_alias=True)

    print(generation)

    # if len(generation['unresolved_params']) > 0:
    #     await handleUnresolvedParams(entrypoint, generation)
    # print("returning from search params")
    return generation

async def handleUnresolvedParams(entrypoint, generation):
    match entrypoint.id:
        case "get_occurrences":
            for params in generation['unresolved_params']:
                if params == 'areaid':
                    pass
        case _:
            pass
    return