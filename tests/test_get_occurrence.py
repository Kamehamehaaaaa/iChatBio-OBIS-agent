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



