import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess
from instructor.core import InstructorRetryException
from entrypoints import statistics


@pytest.mark.asyncio
async def test_statistics_basic_success():
    """Test successful statistics query without extensions."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"species": "brachyura", "year": 2020},
        "clarification_needed": False
    }

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = [{"year": 2020, "count": 10}]

    with patch("entrypoints.statistics.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.statistics.utils.generate_obis_url", return_value="http://fake-url"), \
         patch("entrypoints.statistics.requests.get", return_value=mock_response):

        await statistics.run("Yearly stats for brachyura", mock_context)

    mock_process.create_artifact.assert_awaited_once()
    args, kwargs = mock_process.create_artifact.call_args
    assert kwargs["metadata"]["data_source"] == "OBIS"
    assert kwargs["metadata"]["retrieved_record_count"] == 1


@pytest.mark.asyncio
async def test_statistics_with_extensions():
    """Test statistics query with extensions."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {
            "species": "brachyura",
            "statistics_extensions": ["year", "decade"]
        },
        "clarification_needed": False
    }

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = [{"value": 1}]

    with patch("entrypoints.statistics.search._generate_search_parameters", AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.statistics.utils.generate_obis_url", return_value="http://fake-url"), \
         patch("entrypoints.statistics.requests.get", return_value=mock_response):

        await statistics.run("Trend analysis", mock_context)

    # Should create artifact twice (for 2 extensions)
    assert mock_process.create_artifact.await_count == 2


@pytest.mark.asyncio
async def test_statistics_llm_failure():
    """Test when LLM param generation fails."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    with patch(
        "entrypoints.statistics.search._generate_search_parameters",
        AsyncMock(side_effect=Exception("LLM error"))
    ), patch(
        "entrypoints.statistics.utils.exceptionHandler",
        AsyncMock()
    ) as mock_exception:

        await statistics.run("Invalid request", mock_context)

    mock_exception.assert_awaited_once()
    mock_process.create_artifact.assert_not_awaited()


@pytest.mark.asyncio
async def test_statistics_clarification_needed():
    """Test clarification flow when LLM requests clarification."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {
        "params": {"species": "brachyura"},
        "clarification_needed": True,
        "reason": "Need clarification"
    }

    with patch("entrypoints.statistics.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.statistics.utils.exceptionHandler", AsyncMock()) as mock_exception:

        await statistics.run("Clarify stats", mock_context)

    mock_exception.assert_awaited_once()


@pytest.mark.asyncio
async def test_statistics_resolve_institute():
    """Test institute resolution."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {
        "params": {"institute": "Smithsonian"},
        "clarification_needed": False
    }

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = [{"value": 1}]

    with patch("entrypoints.statistics.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.statistics.utils.resolveParams", AsyncMock(return_value=True)), \
         patch("entrypoints.statistics.utils.generate_obis_url", return_value="http://fake-url"), \
         patch("entrypoints.statistics.requests.get", return_value=mock_response):

        await statistics.run("Stats for Smithsonian", mock_context)

    mock_process.create_artifact.assert_awaited_once()


@pytest.mark.asyncio
async def test_statistics_non_ok_response():
    """Test OBIS API returns non-200."""
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

    with patch("entrypoints.statistics.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.statistics.utils.generate_obis_url", return_value="http://fake-url"), \
         patch("entrypoints.statistics.requests.get", return_value=mock_response):

        await statistics.run("Stats request", mock_context)

    mock_process.create_artifact.assert_not_awaited()
    mock_process.log.assert_any_call("Response code: 500 Internal Server Error - something went wrong!")


@pytest.mark.asyncio
async def test_statistics_instructor_retry_exception():
    """Test handling of InstructorRetryException."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {
        "params": {"species": "brachyura"},
        "clarification_needed": False
    }

    with patch("entrypoints.statistics.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.statistics.utils.generate_obis_url", return_value="http://fake-url"), \
         patch("entrypoints.statistics.requests.get",
               side_effect=InstructorRetryException(messages=["retry"], n_attempts=1,
                                                    total_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})):

        await statistics.run("Stats request", mock_context)

    mock_process.log.assert_any_call("Sorry, I couldn't find any species statistics.")


@pytest.mark.asyncio
async def test_statistics_invalid_json():
    """Test invalid JSON response."""
    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {
        "params": {"species": "brachyura"},
        "clarification_needed": False
    }

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")

    with patch("entrypoints.statistics.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.statistics.utils.generate_obis_url", return_value="http://fake-url"), \
         patch("entrypoints.statistics.requests.get", return_value=mock_response), \
         patch("entrypoints.statistics.utils.exceptionHandler", AsyncMock()) as mock_exception:

        await statistics.run("Stats request", mock_context)

    mock_exception.assert_awaited_once()
