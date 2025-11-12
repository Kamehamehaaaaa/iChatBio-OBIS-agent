import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from instructor.core import InstructorRetryException
from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess
from entrypoints import dataset


@pytest.mark.asyncio
async def test_run_dataset_basic_success():
    """Test successful dataset query."""
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
        "results": [{"id": i} for i in range(3)]
    }

    with patch("entrypoints.dataset.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.dataset.utils.getAreaId", AsyncMock(return_value=[{"areaid": "A1"}])), \
         patch("entrypoints.dataset.requests.get", return_value=mock_response):
        
        await dataset.run("Find datasets of brachyura in Atlantic Ocean", mock_context)

        mock_process.log.assert_any_call("Original request: Find datasets of brachyura in Atlantic Ocean")
        mock_process.create_artifact.assert_awaited_once()
        args, kwargs = mock_process.create_artifact.call_args
        assert kwargs["metadata"]["data_source"] == "OBIS"
        assert kwargs["metadata"]["retrieved_record_count"] == 3
        assert kwargs["metadata"]["total_matching_count"] == 10


@pytest.mark.asyncio
async def test_run_dataset_institute_priority():
    """Test when both institute and area are given (institute takes precedence)."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {
        "params": {"species": "brachyura", "institute": "Smithsonian", "area": "Atlantic"},
        "clarification_needed": False
    }

    mock_institutes = [{"id": "inst1", "name": "Smithsonian", "score": 1.0}]
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {"total": 5, "results": [{"id": 1}]}

    with patch("entrypoints.dataset.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.dataset.utils.getInstituteId", AsyncMock(return_value=mock_institutes)), \
         patch("entrypoints.dataset.requests.get", return_value=mock_response):

        await dataset.run("Get datasets of brachyura from Smithsonian", mock_context)

        mock_process.create_artifact.assert_awaited_once()
        args, kwargs = mock_process.create_artifact.call_args
        assert "instituteid" in kwargs["uris"][0] or "dataset" in kwargs["uris"][0]


@pytest.mark.asyncio
async def test_run_dataset_area_not_found():
    """Test when area is not found in OBIS."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {
        "params": {"species": "brachyura", "area": "Atlantis"},
        "clarification_needed": False
    }

    with patch("entrypoints.dataset.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.dataset.utils.getAreaId", AsyncMock(return_value=[])), \
         patch("entrypoints.dataset.utils.exceptionHandler", AsyncMock()) as mock_exception:

        await dataset.run("Find datasets of brachyura in Atlantis", mock_context)

        mock_exception.assert_awaited_once()
        mock_process.create_artifact.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_dataset_institute_low_confidence():
    """Test multiple institutes with low confidence score."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {"params": {"institute": "Unknown Institute"}, "clarification_needed": False}
    mock_institutes = [
        {"id": "instA", "name": "Institute A", "score": 0.75},
        {"id": "instB", "name": "Institute B", "score": 0.7},
    ]
    mock_response = MagicMock(ok=True, status_code=200)
    mock_response.json.return_value = {"total": 2, "results": [{"id": 1}, {"id": 2}]}

    with patch("entrypoints.dataset.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.dataset.utils.getInstituteId", AsyncMock(return_value=mock_institutes)), \
         patch("entrypoints.dataset.requests.get", return_value=mock_response):

        await dataset.run("Get datasets from an unknown institute", mock_context)
        
        mock_process.log.assert_any_call(
            "OBIS has 2 closest matching institute names with the input. "
            "They are Institute A, Institute B. Records for Institute A will be fetched"
        )


@pytest.mark.asyncio
async def test_dataset_non_ok_response():
    """Test OBIS returns non-200 response."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {"params": {"species": "brachyura"}, "clarification_needed": False}
    mock_response = MagicMock(ok=False, status_code=500)

    with patch("entrypoints.dataset.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.dataset.requests.get", return_value=mock_response):
        await dataset.run("Find datasets for brachyura", mock_context)

    mock_process.log.assert_any_call("Response code: 500 Internal Server Error - something went wrong!")


@pytest.mark.asyncio
async def test_dataset_invalid_json():
    """Test invalid JSON returned from OBIS dataset API."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {"params": {"species": "brachyura"}, "clarification_needed": False}
    mock_response = MagicMock(ok=True, status_code=200)
    mock_response.json.side_effect = ValueError("Invalid JSON")

    with patch("entrypoints.dataset.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.dataset.requests.get", return_value=mock_response), \
         patch("entrypoints.dataset.utils.exceptionHandler", AsyncMock()) as mock_exception:
        await dataset.run("Find datasets of brachyura", mock_context)

    mock_exception.assert_awaited_once()


@pytest.mark.asyncio
async def test_instructor_retry_exception():
    """Test InstructorRetryException handling."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    with patch("entrypoints.dataset.search._generate_search_parameters", AsyncMock(return_value={"params": {}, "clarification_needed": False})), \
         patch("entrypoints.dataset.requests.get", side_effect=InstructorRetryException(messages=["retry"], n_attempts=1, total_usage={})):
        await dataset.run("Retry test", mock_context)
        mock_process.log.assert_any_call("Sorry, I couldn't find any species datasets.")


@pytest.mark.asyncio
async def test_dataset_clarification_needed():
    """Test when LLM requests clarification."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {
        "clarification_needed": True,
        "reason": "Need clarification on dataset type",
        "params": {}
    }

    with patch("entrypoints.dataset.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.dataset.utils.exceptionHandler", AsyncMock()) as mock_exception:
        await dataset.run("Clarify dataset query", mock_context)
        mock_exception.assert_awaited_once()


@pytest.mark.asyncio
async def test_dataset_no_institute_found():
    """Test when no institutes are found in OBIS."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {"params": {"institute": "Fake Institute"}, "clarification_needed": False}

    with patch("entrypoints.dataset.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.dataset.utils.getInstituteId", AsyncMock(return_value=[])):
        await dataset.run("Find datasets from Fake Institute", mock_context)

    mock_process.log.assert_any_call("OBIS doesn't have any institutes named Fake Institute")


@pytest.mark.asyncio
async def test_dataset_multiple_area_matches():
    """Test when multiple areas are matched."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {"params": {"species": "brachyura", "area": "Atlantic"}, "clarification_needed": False}
    mock_areas = [{"areaid": "A1"}, {"areaid": "A2"}]
    mock_response = MagicMock(ok=True, status_code=200)
    mock_response.json.return_value = {"total": 2, "results": [{"id": 1}]}

    with patch("entrypoints.dataset.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.dataset.utils.getAreaId", AsyncMock(return_value=mock_areas)), \
         patch("entrypoints.dataset.requests.get", return_value=mock_response):

        await dataset.run("Find brachyura datasets in Atlantic", mock_context)

    mock_process.log.assert_any_call("Multiple area matches found")