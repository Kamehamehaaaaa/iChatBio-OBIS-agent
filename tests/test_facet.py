import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess
from instructor.core import InstructorRetryException
from entrypoints import facet


@pytest.mark.asyncio
async def test_run_facet_basic_success():
    """Test successful facet query."""

    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"scientificname": "Egregia menziesii", "facet": "datasetid"},
        "clarification_needed": False
    }

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "total": 100,
        "results": {
            "datasetid": [{"value": "ds1", "count": 60}]
        }
    }

    with patch("entrypoints.facet.search._generate_search_parameters",
               AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.facet.utils.generate_obis_url",
               return_value="https://fake-obis.org/facet"), \
         patch("entrypoints.facet.requests.get",
               return_value=mock_response):

        await facet.run("Facet datasets for Egregia menziesii", mock_context)

        mock_process.create_artifact.assert_awaited_once()
        args, kwargs = mock_process.create_artifact.call_args
        assert kwargs["metadata"]["data_source"] == "OBIS"
        assert kwargs["metadata"]["retrieved_flag_count"] == 1
        assert kwargs["metadata"]["total_matching_count"] == 100


@pytest.mark.asyncio
async def test_run_facet_institute_resolution():
    """Test institute name resolution."""

    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"institute": "CSIRO", "facet": "datasetid"},
        "clarification_needed": False
    }

    mock_institutes = [{"id": "123", "name": "CSIRO", "score": 1.0}]

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {"total": 5, "results": {"datasetid": []}}

    with patch("entrypoints.facet.search._generate_search_parameters",
               AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.facet.utils.getInstituteId",
               AsyncMock(return_value=mock_institutes)), \
         patch("entrypoints.facet.utils.generate_obis_url",
               return_value="fake-url?instituteid=123"), \
         patch("entrypoints.facet.requests.get",
               return_value=mock_response):

        await facet.run("Facet by institute CSIRO", mock_context)

        mock_process.create_artifact.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_facet_area_not_found():
    """Test when area lookup fails."""

    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"area": "Atlantis"},
        "clarification_needed": False
    }

    with patch("entrypoints.facet.search._generate_search_parameters",
               AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.facet.utils.getAreaId",
               AsyncMock(return_value=[])), \
         patch("entrypoints.facet.utils.exceptionHandler",
               AsyncMock()) as mock_exception:

        await facet.run("Facet records in Atlantis", mock_context)

        mock_exception.assert_awaited_once()
        mock_process.create_artifact.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_facet_dataset_multiple_matches():
    """Test dataset ambiguity handling."""

    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"facets": ["datasetID"], "datasetname": "reef survey"},
        "clarification_needed": False
    }

    mock_datasets = [
        ("1", "Dataset A"),
        ("2", "Dataset B")
    ]

    with patch("entrypoints.facet.search._generate_search_parameters",
               AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.facet.utils.getDatasetId",
               AsyncMock(return_value=("dataset-url", mock_datasets))):

        await facet.run("Facet reef survey dataset", mock_context)

        mock_process.create_artifact.assert_awaited_once()


# @pytest.mark.asyncio
# async def test_run_facet_commonname_resolution():
#     """Test common name to scientific name conversion."""

#     mock_context = AsyncMock(spec=ResponseContext)
#     mock_process = AsyncMock(spec=IChatBioAgentProcess)
#     mock_context.begin_process.return_value.__aenter__.return_value = mock_process

#     mock_llm_response = {
#         "params": {"commonname": "giant kelp", "facet": "datasetid"},
#         "clarification_needed": False
#     }

#     mock_response = MagicMock()
#     mock_response.ok = True
#     mock_response.status_code = 200
#     mock_response.json.return_value = {"total": 1, "results": {"datasetid": []}}

#     with patch("entrypoints.facet.search._generate_search_parameters",
#                AsyncMock(return_value=mock_llm_response)), \
#          patch("entrypoints.facet.utils.resolveCommonName.get",
#                AsyncMock(return_value=([("giant kelp", "Macrocystis pyrifera")]))), \
#          patch("entrypoints.facet.utils.generate_obis_url",
#                return_value="fake-url"), \
#          patch("entrypoints.facet.requests.get",
#                return_value=mock_response):

#         await facet.run("Facet giant kelp datasets", mock_context)

#         mock_process.create_artifact.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_facet_http_error():
    """Test OBIS returning 500 error."""

    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"scientificname": "Egregia menziesii"},
        "clarification_needed": False
    }

    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 500

    with patch("entrypoints.facet.search._generate_search_parameters",
               AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.facet.utils.generate_obis_url",
               return_value="fake-url"), \
         patch("entrypoints.facet.requests.get",
               return_value=mock_response):

        await facet.run("Facet test HTTP error", mock_context)

        mock_process.create_artifact.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_facet_llm_exception():
    """Test when LLM parameter generation fails."""

    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    with patch("entrypoints.facet.search._generate_search_parameters",
               AsyncMock(side_effect=Exception("LLM failure"))), \
         patch("entrypoints.facet.utils.exceptionHandler",
               AsyncMock()) as mock_exception:

        await facet.run("Invalid facet request", mock_context)

        mock_exception.assert_awaited_once()
        mock_process.create_artifact.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_facet_instructor_retry_exception():
    """Test InstructorRetryException handling."""

    mock_context = AsyncMock(spec=ResponseContext)
    mock_process = AsyncMock(spec=IChatBioAgentProcess)
    mock_context.begin_process.return_value.__aenter__.return_value = mock_process

    mock_llm_response = {
        "params": {"scientificname": "Egregia menziesii"},
        "clarification_needed": False
    }

    with patch("entrypoints.facet.search._generate_search_parameters",
               AsyncMock(return_value=mock_llm_response)), \
         patch("entrypoints.facet.utils.generate_obis_url",
               return_value="fake-url"), \
         patch("entrypoints.facet.requests.get",
               side_effect=InstructorRetryException(
                   messages=["retry"],
                   n_attempts=1,
                   total_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
               )):

        await facet.run("Facet retry test", mock_context)

        mock_process.log.assert_any_call(
            "Sorry, I couldn't find any species occurrences."
        )
