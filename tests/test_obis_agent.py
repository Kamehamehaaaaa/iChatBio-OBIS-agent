import json
import pytest

from agent import OBISAgent
from ichatbio.agent_response import ResponseChannel, ResponseContext, ResponseMessage

from ichatbio.agent_response import ArtifactResponse

class InMemoryResponseChannel(ResponseChannel):
    def __init__(self, message_buffer: list):
        self.message_buffer = message_buffer

    async def submit(self, message: ResponseMessage, context_id: str):
        self.message_buffer.append(message)

def get_context():
    messages = list()
    channel = InMemoryResponseChannel(messages)
    context = ResponseContext(channel, "617727d1-4ce8-4902-884c-db786854b51c")
    return context

def load_test_cases():
    with open("tests/resources/queries.json") as f:
        return json.load(f)


def normalize(obj):
    if isinstance(obj, dict):
        return {k: normalize(v) for k, v in sorted(obj.items()) if v is not None}
    if isinstance(obj, list):
        return sorted(normalize(x) for x in obj)
    return obj

@pytest.mark.asyncio
@pytest.mark.parametrize("case", load_test_cases())
async def test_query_resolution(agent, context, case, messages):
    query = case["query"]
    expected = normalize(case["expected"])

    # if global_context == None:
    #     global_context = get_context()

    await agent.run(context=context, request=query, entrypoint=expected["endpoint"], params=None)

    print(messages)
    # messages1 = [m async for m in messages]
    # result = normalize(result)

    # print(f"\nQuery: {query}\nExpected: {expected}\n \nArtifact: ")

    artifacts = [i for i in messages if type(i) == ArtifactResponse]
    assert len(artifacts) > 0

    urls = []
    for i in artifacts:
        for j in i.uris:
            urls.append(j)

    assert expected["url"] in urls