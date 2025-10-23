# import pytest
# import respx
# import httpx
from ichatbio.agent_response import ArtifactResponse

# @pytest.mark.asyncio
# @respx.mock
# async def test_get_occurrence_brachyura(agent, context, messages):
#     # --- 1️⃣ Mock OBIS API response ---
#     mock_url = "https://api.obis.org/v3/occurrence"
#     mock_response = {
#         "total": 125,
#         "results": [
#             {"scientificName": "Brachyura", "decimalLatitude": 12.3, "decimalLongitude": -45.6}
#         ]
#     }
#     respx.get(mock_url).mock(return_value=httpx.Response(200, json=mock_response))

#     # --- 2️⃣ Run the agent command ---
#     await agent.run(context, "Find occurrences of brachyura", "get_occurrence", None)

#     # --- 3️⃣ Retrieve the artifact response from messages ---
#     print(messages)
#     artifact = next((m for m in messages if isinstance(m, ArtifactResponse)), None)
#     assert artifact, "Expected an ArtifactResponse message to be created."

#     # --- 4️⃣ Validate metadata structure ---
#     assert "total_record_count" in artifact.metadata
#     assert artifact.metadata["total_record_count"] == 125
#     assert isinstance(artifact.metadata["total_record_count"], int)

#     # --- 5️⃣ Validate OBIS result structure ---
#     results = artifact.metadata.get("records", [])
#     assert isinstance(results, list)
#     assert len(results) > 0
#     assert results[0]["scientificName"].lower() == "brachyura"

#     # --- 6️⃣ Optional: sanity check reasoning/params from the LLM ---
#     assert artifact.metadata.get("params") == {"scientificname": "brachyura"}


# import pytest
# from unittest.mock import patch, AsyncMock, MagicMock
# from src.entrypoints.get_occurrence import run, entrypoint
# from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess

# @pytest.mark.asyncio
# async def test_run_occurrence_basic():
#     # Create a dummy context with mocked async logging and artifact creation
#     mock_process = AsyncMock(spec=IChatBioAgentProcess)
#     mock_context = AsyncMock(spec=ResponseContext)
#     mock_context.begin_process.return_value.__aenter__.return_value = mock_process

#     # Mock the LLM call to return predefined parameters
#     mock_llm_response = {
#         'params': {'species': 'brachyura', 'area': 'Atlantic Ocean'},
#         'clarification_needed': False
#     }

#     # Mock OBIS API response
#     mock_response = MagicMock()
#     mock_response.ok = True
#     mock_response.status_code = 200
#     mock_response.json.return_value = {
#         "total": 10,
#         "results": [{"id": i} for i in range(5)]
#     }

#     with patch("src.entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
#          patch("src.entrypoints.get_occurrence.requests.get", return_value=mock_response), \
#          patch("src.entrypoints.get_occurrence.utils.getAreaId", AsyncMock(return_value=[{"areaid": "123"}])), \
#          patch("src.entrypoints.get_occurrence.utils.getInstituteId", AsyncMock(return_value=[{"score": 1.0, "id": "inst1"}])):

#         await run("Find occurrences of brachyura", mock_context)

#         # Check that logs were called
#         mock_process.log.assert_any_call("Original request: Find occurrences of brachyura")
#         mock_process.log.assert_any_call("Generating search parameters for species occurrences")
#         mock_process.log.assert_any_call("Initial params generated", data={'species': 'brachyura', 'areaid': '123'})

#         # Check artifact creation was called
#         mock_process.create_artifact.assert_called_once()



# tests/test_get_occurrence_agent.py
# import pytest
# from unittest.mock import patch, AsyncMock, MagicMock

# @pytest.mark.asyncio
# async def test_agent_run_occurrence(agent, context):
#     """
#     Test the OBISAgent handling an occurrence request, mocking LLM and OBIS API.
#     """
#     # Patch LLM and OBIS API calls
#     mock_llm_response = {
#         'params': {'species': 'brachyura', 'area': 'Atlantic Ocean'},
#         'clarification_needed': False
#     }

#     mock_response = MagicMock()
#     mock_response.ok = True
#     mock_response.status_code = 200
#     mock_response.json.return_value = {
#         "total": 10,
#         "results": [{"id": i} for i in range(5)]
#     }

#     with patch("src.entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
#          patch("src.entrypoints.get_occurrence.requests.get", return_value=mock_response), \
#          patch("src.entrypoints.get_occurrence.utils.getAreaId", AsyncMock(return_value=[{"areaid": "123"}])), \
#          patch("src.entrypoints.get_occurrence.utils.getInstituteId", AsyncMock(return_value=[{"score": 1.0, "id": "inst1"}])):

#         # Run the agent as it would in production
#         await agent.run(context, "Find occurrences of brachyura", entrypoint_id="get_occurrence", metadata=None)

#         # Assert that messages were generated
#         assert any("OBIS returned the following data for the query" in msg.text for msg in context.channel.message_buffer)
#         # You can also check that the artifact creation occurred
#         assert any(hasattr(msg, "metadata") and msg.metadata.get("data_source") == "OBIS" for msg in context.channel.message_buffer)



# tests/test_get_occurrence_agent.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

# Use relative imports based on sys.path from conftest.py
from entrypoints import get_occurrence
from agent import OBISAgent
from conftest import TEST_CONTEXT_ID

@pytest.mark.asyncio
async def test_agent_run_occurrence(agent, context, messages):
    """
    Test the OBISAgent handling an occurrence request, mocking LLM and OBIS API.
    """

    # 1️⃣ Mock LLM (_generate_search_parameters)
    mock_llm_response = {
        'params': {'species': 'brachyura', 'area': 'Atlantic Ocean'},
        'clarification_needed': False
    }

    # 2️⃣ Mock OBIS API response
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "total": 10,
        "results": [{"id": i} for i in range(5)]
    }

    # 3️⃣ Patch all external calls
    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.get_occurrence.requests.get", return_value=mock_response), \
         patch("entrypoints.get_occurrence.utils.getAreaId", AsyncMock(return_value=[{"areaid": "123"}])), \
         patch("entrypoints.get_occurrence.utils.getInstituteId", AsyncMock(return_value=[{"score": 1.0, "id": "inst1"}])):

        # Run the agent through the get_occurrence entrypoint
        await agent.run(
            context,
            "Find occurrences of brachyura",
            "get_occurrence",
            None
        )

        # 4️⃣ Assertions: check messages were generated
        print(messages)
        messages_text = [
            msg.description for msg in messages if isinstance(msg, ArtifactResponse)
        ]
        assert any("OBIS returned the following data for the query" in t for t in messages_text)

        # Check that artifact metadata exists
        messages_meta = [
            msg.metadata for msg in messages if isinstance(msg, ArtifactResponse)
        ]
        assert any(meta.get("data_source") == "OBIS" for meta in messages_meta)
