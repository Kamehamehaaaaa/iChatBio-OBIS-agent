import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess
from entrypoints import taxon


@pytest.mark.asyncio
async def test_taxon_scientific_name_success():
    """ Test normal scientific name query returning records from OBIS."""

    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    # Mock LLM response from search parameter generator
    llm_response = {
        "params": {"scientificname": "Salmo salar"},
        "clarification_needed": False,
    }

    # Mock a fake OBIS response
    mock_response = MagicMock(ok=True, status_code=200)
    mock_response.json.return_value = {
        "total": 12,
        "results": [{"id": 1, "name": "Salmo salar"}],
    }

    with patch("entrypoints.taxon.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.taxon.requests.get", return_value=mock_response):

        await taxon.run("Get taxon info for Atlantic salmon", mock_context)

    for call in mock_process.log.call_args_list:
        print(call)

    # --- Assertions ---
    mock_process.log.assert_any_call("Original request: Get taxon info for Atlantic salmon")
    mock_process.log.assert_any_call("Querying OBIS")
    mock_process.create_artifact.assert_called_once()
    artifact_call = mock_process.create_artifact.call_args.kwargs
    assert artifact_call["metadata"]["retrieved_record_count"] == 1
    assert artifact_call["metadata"]["total_matching_count"] == 12


@pytest.mark.asyncio
async def test_taxon_common_name_multiple_matches():
    """ Test case when a common name yields multiple scientific name matches."""

    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    llm_response = {
        "params": {"commonname": "salmon"},
        "clarification_needed": False,
    }

    mock_scientific_names = [
        ("Atlantic salmon", "Salmo salar"),
        ("Chinook salmon", "Oncorhynchus tshawytscha"),
    ]

    mock_response = MagicMock(ok=True, status_code=200)
    mock_response.json.return_value = {"total": 2, "results": [{"id": 1}, {"id": 2}]}

    with patch("entrypoints.taxon.search._generate_search_parameters", AsyncMock(return_value=llm_response)), \
         patch("entrypoints.taxon.utils.getScientificName", AsyncMock(return_value=("fake_url", mock_scientific_names))), \
         patch("entrypoints.taxon.requests.get", return_value=mock_response):

        await taxon.run("Get taxon info for salmon", mock_context)

    mock_process.log.assert_any_call("Original request: Get taxon info for salmon")
    # You could also test the log message showing multiple matches:
    log_texts = [str(call) for call in mock_process.log.call_args_list]
    assert any("Multiple scientific name matches found" in log for log in log_texts)
    mock_process.create_artifact.assert_called_once()


@pytest.mark.asyncio
async def test_taxon_invalid_request(monkeypatch):
    """ Test that invalid request raises and logs exception."""

    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    # Force an error in parameter generation
    with patch("entrypoints.taxon.search._generate_search_parameters", AsyncMock(side_effect=Exception("LLM failure"))), \
         patch("entrypoints.taxon.utils.exceptionHandler", AsyncMock()) as mock_handler:
        await taxon.run("invalid query", mock_context)

    mock_handler.assert_awaited()
