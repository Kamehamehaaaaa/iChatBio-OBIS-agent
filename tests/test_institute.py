import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess
from instructor.core import InstructorRetryException
from entrypoints import institute


@pytest.mark.asyncio
async def test_institute_basic_success():
    """Test successful institute query."""
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
    mock_response.json.return_value = {
        "total": 5,
        "results": [{"id": i} for i in range(3)]
    }

    with patch("entrypoints.institute.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.institute.utils.generate_obis_url", return_value="http://fake-url"), \
         patch("entrypoints.institute.requests.get", return_value=mock_response):

        await institute.run("Get institutes with brachyura", mock_context)

    mock_process.create_artifact.assert_awaited_once()
    args, kwargs = mock_process.create_artifact.call_args
    assert kwargs["metadata"]["retrieved_record_count"] == 3
    assert kwargs["metadata"]["total_matching_count"] == 5
    assert kwargs["metadata"]["data_source"] == "OBIS"


@pytest.mark.asyncio
async def test_institute_llm_exception():
    """Test failure in LLM param generation."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    with patch(
        "entrypoints.institute.search._generate_search_parameters",
        AsyncMock(side_effect=Exception("LLM failed"))
    ), patch("entrypoints.institute.utils.exceptionHandler", AsyncMock()):
        await institute.run("Invalid request", mock_context)
        institute.utils.exceptionHandler.assert_awaited_once()
    
    # mock_process.log.assert_any_call("LLM failed Error generating params.")
    mock_process.create_artifact.assert_not_awaited()


@pytest.mark.asyncio
async def test_institute_clarification_needed():
    """Test clarification_needed flow."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {
        "params": {"species": "brachyura"},
        "clarification_needed": True,
        "reason": "Need clarification"
    }

    with patch("entrypoints.institute.search._generate_search_parameters", AsyncMock(return_value=llm_response)),\
        patch("entrypoints.institute.utils.exceptionHandler", AsyncMock()):
        await institute.run("Clarify institute request", mock_context)
        institute.utils.exceptionHandler.assert_awaited_once()

    mock_process.create_artifact.assert_not_awaited()


@pytest.mark.asyncio
async def test_institute_not_found():
    """Test when institute lookup returns empty."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {
        "params": {"institute": "Fake Institute"},
        "clarification_needed": False
    }

    with patch("entrypoints.institute.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.institute.utils.getInstituteId", AsyncMock(return_value=[])):

        await institute.run("Fake Institute records", mock_context)

    mock_process.log.assert_any_call(
        "OBIS doesn't have any institutes named Fake Institute"
    )
    mock_process.create_artifact.assert_not_awaited()


@pytest.mark.asyncio
async def test_institute_low_score_multiple():
    """Test low confidence multiple institute matches."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {
        "params": {"institute": "Unknown Institute"},
        "clarification_needed": False
    }

    mock_institutes = [
        {"id": "inst1", "name": "Institute A", "score": 0.75},
        {"id": "inst2", "name": "Institute B", "score": 0.70}
    ]

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {"total": 2, "results": [{"id": 1}]}

    with patch("entrypoints.institute.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.institute.utils.getInstituteId", AsyncMock(return_value=mock_institutes)), \
         patch("entrypoints.institute.utils.generate_obis_url", return_value="http://fake-url"), \
         patch("entrypoints.institute.requests.get", return_value=mock_response):

        await institute.run("Unknown institute records", mock_context)

    mock_process.log.assert_any_call(
        "OBIS has 2 closest matching institute names with the input. "
        "They are Institute A, Institute B. "
        "Records for Institute A will be fetched"
    )
    mock_process.create_artifact.assert_awaited_once()


@pytest.mark.asyncio
async def test_institute_area_not_found():
    """Test area resolution failure."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {
        "params": {"area": "Atlantis"},
        "clarification_needed": False
    }

    with patch("entrypoints.institute.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.institute.utils.getAreaId", AsyncMock(return_value=[])), \
         patch("entrypoints.institute.utils.exceptionHandler", AsyncMock()) as mock_exception:

        await institute.run("Institute records in Atlantis", mock_context)

    mock_exception.assert_awaited_once()
    mock_process.create_artifact.assert_not_awaited()


@pytest.mark.asyncio
async def test_institute_multiple_area_matches():
    """Test multiple area matches."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {
        "params": {"area": "Atlantic"},
        "clarification_needed": False
    }

    mock_areas = None,[{"id": "A1"}, {"id": "A2"}]

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {"total": 1, "results": [{"id": 1}]}

    with patch("entrypoints.institute.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.institute.utils.getAreaId", AsyncMock(return_value=mock_areas)), \
         patch("entrypoints.institute.utils.generate_obis_url", return_value="http://fake-url"), \
         patch("entrypoints.institute.requests.get", return_value=mock_response):

        await institute.run("Institutes in Atlantic", mock_context)

    mock_process.log.assert_any_call("Multiple area matches found")


@pytest.mark.asyncio
async def test_institute_non_ok_response():
    """Test non-200 OBIS response."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {
        "params": {"species": "brachyura"},
        "clarification_needed": False
    }

    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 500

    with patch("entrypoints.institute.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.institute.utils.generate_obis_url", return_value="http://fake-url"), \
         patch("entrypoints.institute.requests.get", return_value=mock_response):

        await institute.run("Institute records", mock_context)

    mock_process.log.assert_any_call(
        "Response code: 500 Internal Server Error - something went wrong!"
    )
    mock_process.create_artifact.assert_not_awaited()


@pytest.mark.asyncio
async def test_institute_instructor_retry_exception():
    """Test InstructorRetryException handling."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {
        "params": {"species": "brachyura"},
        "clarification_needed": False
    }

    with patch("entrypoints.institute.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.institute.utils.generate_obis_url", return_value="http://fake-url"), \
         patch("entrypoints.institute.requests.get",
               side_effect=InstructorRetryException(messages=["retry"], n_attempts=1,
                                                    total_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})):

        await institute.run("Institute stats request", mock_context)

    mock_process.log.assert_any_call(
        "Sorry, I couldn't find any institutes."
    )
