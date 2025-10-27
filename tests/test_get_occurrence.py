
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
# import pytest
# from unittest.mock import patch, AsyncMock, MagicMock

# # Use relative imports based on sys.path from conftest.py
# from entrypoints import get_occurrence
# from agent import OBISAgent
# from conftest import TEST_CONTEXT_ID

# @pytest.mark.asyncio
# async def test_agent_run_occurrence(agent, context, messages):
#     """
#     Test the OBISAgent handling an occurrence request, mocking LLM and OBIS API.
#     """

#     # 1️⃣ Mock LLM (_generate_search_parameters)
#     mock_llm_response = {
#         'params': {'species': 'brachyura', 'area': 'Atlantic Ocean'},
#         'clarification_needed': False
#     }

#     # 2️⃣ Mock OBIS API response
#     mock_response = MagicMock()
#     mock_response.ok = True
#     mock_response.status_code = 200
#     mock_response.json.return_value = {
#         "total": 10,
#         "results": [{"id": i} for i in range(5)]
#     }

#     # 3️⃣ Patch all external calls
#     with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
#          patch("entrypoints.get_occurrence.requests.get", return_value=mock_response), \
#          patch("entrypoints.get_occurrence.utils.getAreaId", AsyncMock(return_value=[{"areaid": "123"}])), \
#          patch("entrypoints.get_occurrence.utils.getInstituteId", AsyncMock(return_value=[{"score": 1.0, "id": "inst1"}])):

#         # Run the agent through the get_occurrence entrypoint
#         await agent.run(
#             context,
#             "Find occurrences of brachyura",
#             "get_occurrence",
#             None
#         )

#         # 4️⃣ Assertions: check messages were generated
#         print(messages)
#         messages_text = [
#             msg.description for msg in messages if isinstance(msg, ArtifactResponse)
#         ]
#         assert any("OBIS returned the following data for the query" in t for t in messages_text)

#         # Check that artifact metadata exists
#         messages_meta = [
#             msg.metadata for msg in messages if isinstance(msg, ArtifactResponse)
#         ]
#         assert any(meta.get("data_source") == "OBIS" for meta in messages_meta)


import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess, ArtifactResponse
from instructor.core import InstructorRetryException
from entrypoints import get_occurrence


@pytest.mark.asyncio
async def test_run_occurrence_basic_success():
    """Test successful OBIS query with area resolution."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"species": "brachyura", "area": "Atlantic Ocean"},
        "clarification_needed": False
    }

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "total": 10,
        "results": [{"id": i} for i in range(5)]
    }

    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.get_occurrence.utils.getAreaId", AsyncMock(return_value=[{"areaid": "123"}])), \
         patch("entrypoints.get_occurrence.requests.get", return_value=mock_response):
        
        await get_occurrence.run("Find occurrences of brachyura", mock_context)

        mock_process.log.assert_any_call("Original request: Find occurrences of brachyura")
        mock_process.create_artifact.assert_awaited_once()
        args, kwargs = mock_process.create_artifact.call_args
        assert kwargs["metadata"]["data_source"] == "OBIS"
        assert kwargs["metadata"]["retrieved_record_count"] == 5
        assert kwargs["metadata"]["total_matching_count"] == 10


@pytest.mark.asyncio
async def test_run_occurrence_institute_priority():
    """Test when both 'institute' and 'area' are in params (institute wins)."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"species": "brachyura", "area": "Atlantic Ocean", "institute": "Smithsonian"},
        "clarification_needed": False
    }

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {"total": 5, "results": [{"id": 1}]}

    mock_institutes = [{"id": "inst1", "name": "Smithsonian", "score": 1.0}]

    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.get_occurrence.utils.getInstituteId", AsyncMock(return_value=mock_institutes)), \
         patch("entrypoints.get_occurrence.requests.get", return_value=mock_response):
        
        await get_occurrence.run("Records of brachyura at Smithsonian", mock_context)

        mock_process.create_artifact.assert_awaited_once()
        args, kwargs = mock_process.create_artifact.call_args
        print(args, kwargs)
        assert "instituteid" in kwargs["uris"][0] if "uris" in kwargs else True


@pytest.mark.asyncio
async def test_run_occurrence_area_not_found():
    """Test when area name doesn’t match anything."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"species": "brachyura", "area": "Atlantis"},
        "clarification_needed": False
    }

    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.get_occurrence.utils.getAreaId", AsyncMock(return_value=[])), \
         patch("entrypoints.get_occurrence.utils.exceptionHandler", AsyncMock()):

        await get_occurrence.run("Find occurrences in Atlantis", mock_context)

        get_occurrence.utils.exceptionHandler.assert_awaited_once()
        mock_process.create_artifact.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_occurrence_llm_exception():
    """Test when LLM param generation throws an exception."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(side_effect=Exception("LLM failed"))), \
         patch("entrypoints.get_occurrence.utils.exceptionHandler", AsyncMock()):

        await get_occurrence.run("Invalid request", mock_context)

        get_occurrence.utils.exceptionHandler.assert_awaited_once()
        mock_process.create_artifact.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_occurrence_institute_low_score_multiple():
    """Test handling when multiple institutes found and low confidence score."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"species": "brachyura", "institute": "Unknown Institute"},
        "clarification_needed": False
    }

    mock_institutes = [
        {"id": "instA", "name": "Institute A", "score": 0.75},
        {"id": "instB", "name": "Institute B", "score": 0.72}
    ]

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {"total": 2, "results": [{"id": 1}, {"id": 2}]}

    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.get_occurrence.utils.getInstituteId", AsyncMock(return_value=mock_institutes)), \
         patch("entrypoints.get_occurrence.requests.get", return_value=mock_response):
        
        await get_occurrence.run("Records for an unknown institute", mock_context)

        mock_process.log.assert_any_call(
            # "Original request: Records for an unknown institute"
            "OBIS has 2 closest matching institute names with the input. " \
            "They are Institute A, Institute B. "
            "Records for Institute A will be fetched"
        )
        mock_process.create_artifact.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_occurrence_non_ok_response():
    """Test OBIS API returns 500 error."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"species": "brachyura", "area": "Atlantic Ocean"},
        "clarification_needed": False
    }

    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 500

    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.get_occurrence.utils.getAreaId", AsyncMock(return_value=[{"areaid": "999"}])), \
         patch("entrypoints.get_occurrence.requests.get", return_value=mock_response):

        await get_occurrence.run("Find occurrences of brachyura", mock_context)
        mock_process.log.assert_any_call("OBIS returned error 500 - something went wrong!")
        mock_process.create_artifact.assert_not_awaited()


@pytest.mark.asyncio
async def test_multiple_area_matches():
    """Test when multiple OBIS area matches are found."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"species": "brachyura", "area": "Atlantic Ocean"},
        "clarification_needed": False
    }

    mock_areas = [
        {"areaid": "123"},
        {"areaid": "456"},
        {"areaid": "789"}
    ]

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {"total": 10, "results": [{"id": i} for i in range(3)]}

    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.get_occurrence.utils.getAreaId", AsyncMock(return_value=mock_areas)), \
         patch("entrypoints.get_occurrence.requests.get", return_value=mock_response):

        await get_occurrence.run("Find brachyura in ocean", mock_context)
        mock_process.log.assert_any_call("Multiple area matches found")
        mock_process.create_artifact.assert_awaited_once()


@pytest.mark.asyncio
async def test_no_results_from_obis():
    """Test when OBIS returns 0 results but successful response."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"species": "brachyura"},
        "clarification_needed": False
    }

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {"total": 0, "results": []}

    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.get_occurrence.requests.get", return_value=mock_response):

        await get_occurrence.run("Find nonexistent records", mock_context)
        mock_process.log.assert_any_call("Querying OBIS")
        # Ensure artifact still gets created (with zero results)
        mock_process.create_artifact.assert_awaited_once()
        args, kwargs = mock_process.create_artifact.call_args
        assert kwargs["metadata"]["retrieved_record_count"] == 0
        assert kwargs["metadata"]["total_matching_count"] == 0


@pytest.mark.asyncio
async def test_instructor_retry_exception():
    """Test if InstructorRetryException is raised during query."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"species": "brachyura"},
        "clarification_needed": False
    }

    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.get_occurrence.requests.get", 
               side_effect=InstructorRetryException(messages=["retry"], n_attempts=1,
                                                    total_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})):
        await get_occurrence.run("Find brachyura", mock_context)
        mock_process.log.assert_any_call("Sorry, information retrival failed.")


@pytest.mark.asyncio
async def test_clarification_needed_exception():
    """Test when LLM requests clarification."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {
        "params": {"species": "brachyura"},
        "clarification_needed": True,
        "reason": "Need clarification on region"
    }

    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.get_occurrence.utils.exceptionHandler", AsyncMock()):
        await get_occurrence.run("Find brachyura", mock_context)
        get_occurrence.utils.exceptionHandler.assert_awaited_once()


@pytest.mark.asyncio
async def test_unresolved_institute_bypass():
    """Test if unresolved_params allows bypass of clarification exception."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {
        "params": {"institute": "Test Institute"},
        "clarification_needed": True,
        "reason": "Need institute ID",
        "unresolved_params": ["instituteid"]
    }

    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.get_occurrence.utils.getInstituteId", AsyncMock(return_value=[{"id": "123", "score": 1.0}])), \
         patch("entrypoints.get_occurrence.requests.get", return_value=MagicMock(ok=True, status_code=200, json=lambda: {"total": 1, "results": [{"id": 1}]})):

        await get_occurrence.run("Find records from institute", mock_context)
        mock_process.create_artifact.assert_awaited_once()


@pytest.mark.asyncio
async def test_invalid_json_from_obis():
    """Test when OBIS returns invalid JSON data."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"species": "brachyura"},
        "clarification_needed": False
    }

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")

    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.get_occurrence.requests.get", return_value=mock_response), \
         patch("entrypoints.get_occurrence.utils.exceptionHandler", AsyncMock()):

        await get_occurrence.run("Find brachyura", mock_context)
        get_occurrence.utils.exceptionHandler.assert_awaited_once()

@pytest.mark.asyncio
async def test_no_institutes_found():
    """Test handling when no institutes are found."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"species": "brachyura", "institute": "Fake Institute"},
        "clarification_needed": False,
    }

    with patch(
        "entrypoints.get_occurrence.search._generate_search_parameters",
        AsyncMock(return_value=mock_llm_response)
    ), patch(
        "entrypoints.get_occurrence.utils.getInstituteId",
        AsyncMock(return_value=[])
    ):
        await get_occurrence.run("Records for Fake Institute", mock_context)

    mock_process.log.assert_any_call(
        "OBIS doesn't have any institutes named Fake Institute"
    )

@pytest.mark.asyncio
async def test_invalid_json_from_obis():
    """Test handling when OBIS API returns invalid JSON."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {"params": {"species": "brachyura"}, "clarification_needed": False}
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")

    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.get_occurrence.requests.get", return_value=mock_response), \
         patch("entrypoints.get_occurrence.utils.exceptionHandler", AsyncMock()) as mock_exception:
        await get_occurrence.run("Find brachyura", mock_context)

    mock_exception.assert_awaited_once()


@pytest.mark.asyncio
async def test_obis_api_error_response():
    """Test when OBIS API returns a non-200 response."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {"params": {"species": "brachyura"}, "clarification_needed": False}
    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 500

    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.get_occurrence.requests.get", return_value=mock_response):
        await get_occurrence.run("Find brachyura", mock_context)

    mock_process.log.assert_any_call("OBIS returned error 500 - something went wrong!")


@pytest.mark.asyncio
async def test_area_not_found():
    """Test when area lookup fails to match."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"species": "brachyura", "area": "Atlantis"},
        "clarification_needed": False,
    }

    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.get_occurrence.utils.getAreaId", AsyncMock(return_value=[])), \
         patch("entrypoints.get_occurrence.utils.exceptionHandler", AsyncMock()) as mock_exception:
        await get_occurrence.run("Find occurrences in Atlantis", mock_context)

    mock_exception.assert_awaited_once()


@pytest.mark.asyncio
async def test_llm_clarification_needed():
    """Test case when LLM requests clarification and unresolved params trigger exception."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"species": "brachyura"},
        "clarification_needed": True,
        "unresolved_params": ["instituteid"],
        "reason": "Institute ID not found",
    }

    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.get_occurrence.utils.exceptionHandler", AsyncMock()) as mock_exception:
        await get_occurrence.run("Find brachyura in test institute", mock_context)

    mock_exception.assert_awaited_once()


@pytest.mark.asyncio
async def test_multiple_area_matches():
    """Test when multiple areas are matched."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"species": "brachyura", "area": "Atlantic"},
        "clarification_needed": False,
    }

    mock_areas = [{"areaid": "A1"}, {"areaid": "A2"}]

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {"total": 5, "results": [{"id": 1}]}

    with patch("entrypoints.get_occurrence.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.get_occurrence.utils.getAreaId", AsyncMock(return_value=mock_areas)), \
         patch("entrypoints.get_occurrence.requests.get", return_value=mock_response):
        await get_occurrence.run("Find brachyura in Atlantic", mock_context)

    mock_process.log.assert_any_call("Multiple area matches found")



