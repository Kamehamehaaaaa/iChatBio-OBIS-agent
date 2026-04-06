import json
import pytest
from deepeval.evaluate import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from ichatbio.agent_response import ArtifactResponse

import requests

def load_test_cases():
    with open("tests/resources/queries.json") as f:
        return json.load(f)

def normalize(obj):
    if isinstance(obj, dict):
        return {k: normalize(v) for k, v in sorted(obj.items()) if v is not None}
    if isinstance(obj, list):
        return sorted(normalize(x) for x in obj)
    return obj


relevance = GEval(
    name="OBIS Retrieval Relevance",
    criteria="Check whether the 'actual output' has the details or would be a response or an adequate answer to the 'input'." \
            "Cosmetic differences like missing context to query, or missing explanation of returned data are okay." \
            "The records retrieved are marin records and always from OBIS.",
    # evaluation_steps=[
    #     "Check whether the response numerically answers the user's query.",
    #     "If the query asks for year-wise counts, verify that response contains counts grouped by year.",
    #     "Do not require textual explanations.",
    #     "Assume API source is correct.",
    #     "Focus only on semantic alignment between query and response."
    # ],
    evaluation_params=[
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.INPUT
    ],
    model="gpt-4.1-nano",
)

@pytest.mark.asyncio
@pytest.mark.parametrize("case", load_test_cases())
async def test_query_resolution(agent, context, case, messages):
    query = case["query"]
    expected = normalize(case["expected"])

    await agent.run(context=context, request=query, entrypoint=case["endpoint"], params=None)

    print(messages)

    artifacts = [i for i in messages if type(i) == ArtifactResponse]
    assert len(artifacts) > 0

    urls = []
    for i in artifacts:
        for j in i.uris:
            urls.append(j)

    assert expected["url"] in urls

    # try:
    response = requests.get(urls[0], timeout=10)

    response_json = response.json()

    response_text = json.dumps(response_json[:5] if isinstance(response_json, list) else response_json)[:4500]

    print(response_text)
    
    test_case = LLMTestCase(
        input=query,
        actual_output=response_text
    )

    result = relevance.measure(test_case)

    print(f"\nQuery: {query}")
    print(f"URL: {urls[0]}")
    print(f"Score: {result}")
    print(f"Reason: {relevance.reason}\n")

    assert result >= 0.5

    # except Exception as e:
    #     print(e)