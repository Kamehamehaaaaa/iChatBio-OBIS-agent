import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess
from instructor.core import InstructorRetryException
from entrypoints import institute_lookup


@pytest.mark.asyncio
async def test_run_institute_basic_success():
    """Test successful institute lookup with area resolution."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"institute": "Smithsonian Institution", "area": "Atlantic Ocean"},
        "clarification_needed": False
    }

    mock_institute = [{"id": "inst1", "name": "Smithsonian Institution", "score": 1.0}]
    mock_area = [{"areaid": "123"}]

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "total": 10,
        "results": [{"id": i} for i in range(5)]
    }

    with patch("entrypoints.institute_lookup.search._generate_search_parameters",
               AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.institute_lookup.utils.getInstituteId",
               AsyncMock(return_value=mock_institute)), \
         patch("entrypoints.institute_lookup.utils.getAreaId",
               AsyncMock(return_value=mock_area)), \
         patch("entrypoints.institute_lookup.utils.generate_obis_extension_url",
               return_value="http://fake-url"), \
         patch("entrypoints.institute_lookup.requests.get",
               return_value=mock_response):

        await institute_lookup.run("Records at Smithsonian in Atlantic", mock_context)

        mock_process.log.assert_any_call("Original request: Records at Smithsonian in Atlantic")
        mock_process.create_artifact.assert_awaited_once()

        _, kwargs = mock_process.create_artifact.call_args
        assert kwargs["metadata"]["data_source"] == "OBIS"
        assert kwargs["metadata"]["retrieved_record_count"] == 5
        assert kwargs["metadata"]["total_matching_count"] == 10


@pytest.mark.asyncio
async def test_run_institute_not_found():
    """Test when no matching institutes are found."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"institute": "Fake Institute"},
        "clarification_needed": False
    }

    with patch("entrypoints.institute_lookup.search._generate_search_parameters",
               AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.institute_lookup.utils.getInstituteId",
               AsyncMock(return_value=[])):

        await institute_lookup.run("Records at Fake Institute", mock_context)

        mock_process.log.assert_any_call(
            "OBIS doesn't have any institutes named Fake Institute"
        )
        mock_process.create_artifact.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_institute_low_score_multiple_matches():
    """Test multiple institute matches with low confidence score."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"institute": "Unknown Institute"},
        "clarification_needed": False
    }

    mock_institutes = [
        {"id": "instA", "name": "Institute A", "score": 0.75},
        {"id": "instB", "name": "Institute B", "score": 0.72}
    ]

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {"total": 2, "results": [{"id": 1}]}

    with patch("entrypoints.institute_lookup.search._generate_search_parameters",
               AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.institute_lookup.utils.getInstituteId",
               AsyncMock(return_value=mock_institutes)), \
         patch("entrypoints.institute_lookup.utils.generate_obis_extension_url",
               return_value="http://fake-url"), \
         patch("entrypoints.institute_lookup.requests.get",
               return_value=mock_response):

        await institute_lookup.run("Records for unknown institute", mock_context)

        mock_process.log.assert_any_call(
            "OBIS has 2 closest matching institute names with the input. "
            "They are Institute A, Institute B. Information about Institute A will be fetched"
        )
        mock_process.create_artifact.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_area_not_found():
    """Test when area lookup fails."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"area": "Atlantis"},
        "clarification_needed": False
    }

    with patch("entrypoints.institute_lookup.search._generate_search_parameters",
               AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.institute_lookup.utils.getAreaId",
               AsyncMock(return_value=[])), \
         patch("entrypoints.institute_lookup.utils.exceptionHandler",
               AsyncMock()) as mock_exception:

        await institute_lookup.run("Institutes in Atlantis", mock_context)

        mock_exception.assert_awaited_once()
        mock_process.create_artifact.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_non_ok_response():
    """Test OBIS API returning 500 error."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"institute": "Smithsonian"},
        "clarification_needed": False
    }

    mock_institute = [{"id": "inst1", "name": "Smithsonian", "score": 1.0}]

    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 500

    with patch("entrypoints.institute_lookup.search._generate_search_parameters",
               AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.institute_lookup.utils.getInstituteId",
               AsyncMock(return_value=mock_institute)), \
         patch("entrypoints.institute_lookup.utils.generate_obis_extension_url",
               return_value="http://fake-url"), \
         patch("entrypoints.institute_lookup.requests.get",
               return_value=mock_response):

        await institute_lookup.run("Records at Smithsonian", mock_context)

        mock_process.log.assert_any_call("Response code: 500 Internal Server Error - something went wrong!")
        mock_process.create_artifact.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_llm_exception():
    """Test when LLM param generation fails."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    with patch("entrypoints.institute_lookup.search._generate_search_parameters",
               AsyncMock(side_effect=Exception("LLM failed"))), \
        patch("entrypoints.institute_lookup.utils.exceptionHandler", AsyncMock()):

        await institute_lookup.run("Invalid request", mock_context)

        institute_lookup.utils.exceptionHandler.assert_awaited_once()
        mock_process.create_artifact.assert_not_awaited()


@pytest.mark.asyncio
async def test_instructor_retry_exception():
    """Test InstructorRetryException during OBIS query."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"institute": "Smithsonian"},
        "clarification_needed": False
    }

    mock_institute = [{"id": "inst1", "name": "Smithsonian", "score": 1.0}]

    with patch("entrypoints.institute_lookup.search._generate_search_parameters",
               AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.institute_lookup.utils.getInstituteId",
               AsyncMock(return_value=mock_institute)), \
         patch("entrypoints.institute_lookup.utils.generate_obis_extension_url",
               return_value="http://fake-url"), \
         patch("entrypoints.institute_lookup.requests.get",
               side_effect=InstructorRetryException(
                   messages=["retry"],
                   n_attempts=1,
                   total_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
               )):

        await institute_lookup.run("Records at Smithsonian", mock_context)

        mock_process.log.assert_any_call("Sorry, I couldn't find any species datasets.")
