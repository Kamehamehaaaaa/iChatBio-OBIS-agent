# def validate_response(request, response):


# utils/validation.py

from typing import List, Dict, Any, Optional
import re
import json
from openai import AsyncOpenAI
from utils import utils


# =========================
# Rule-based validators
# =========================

def validate_intent_alignment(request: str, params: Dict[str, Any]) -> List[str]:
    """
    Check if user intent is reflected in generated parameters.
    Soft validation (warnings).
    """
    issues = []
    req = request.lower()

    # species intent
    species_keywords = ["species", "occurrence", "taxon", "records", "brachyura", "crab", "fish"]
    if any(k in req for k in species_keywords):
        if not any(k in params for k in ["scientificname", "id", "taxonid"]):
            issues.append("User intent suggests species query, but no taxon filter present.")

    # area intent
    if any(k in req for k in ["ocean", "sea", "atlantic", "pacific", "area", "region"]):
        if "areaid" not in params:
            issues.append("User intent suggests area filter, but areaid not present.")

    # institute intent
    if "institute" in req or "university" in req or "museum" in req:
        if "instituteid" not in params:
            issues.append("User intent suggests institute filter, but instituteid not present.")

    # dataset intent
    if "dataset" in req:
        if "datasetid" not in params:
            issues.append("User intent suggests dataset query, but datasetid not present.")

    return issues


def validate_url(url: str, expected_endpoint: str) -> List[str]:
    """
    Hard validation for wrong endpoint usage.
    """
    issues = []
    if expected_endpoint not in url:
        issues.append(f"Wrong OBIS endpoint used. Expected '{expected_endpoint}' in URL.")
    if "None" in url or "null" in url:
        issues.append("URL contains null/None values.")
    return issues


def validate_response_consistency(params: Dict[str, Any], response_json: Dict[str, Any]) -> List[str]:
    """
    Validate logical consistency of OBIS response.
    """
    issues = []
    total = response_json.get("total", 0)
    results = response_json.get("results", [])

    if total > 0 and len(results) == 0:
        issues.append("OBIS returned total > 0 but empty results (pagination or limit issue).")

    # Taxon consistency check
    if "scientificname" in params and results:
        target = params["scientificname"].lower()
        matches = 0
        for r in results[:10]:
            name = (
                r.get("scientificName")
                or r.get("scientificname")
                or ""
            ).lower()
            if target in name:
                matches += 1
        if matches == 0:
            issues.append("Returned records do not match scientificname filter.")

    return issues


# =========================
# Unified validator
# =========================

def validate_obis_result(
    request: str,
    params: Dict[str, Any],
    url: str,
    response_json: Dict[str, Any],
    endpoint: str,
) -> Dict[str, Any]:
    """
    Unified validation output.
    """
    hard_errors = []
    warnings = []

    hard_errors += validate_url(url, endpoint)
    warnings += validate_intent_alignment(request, params)
    warnings += validate_response_consistency(params, response_json)

    return {
        "valid": len(hard_errors) == 0,
        "hard_errors": hard_errors,
        "warnings": warnings,
    }


# =========================
# LLM-based evaluator
# =========================

class LLMValidator:
    """
    LLM judge for semantic correctness.
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=utils.getValue("OPEN_API_KEY"), base_url=utils.getValue("OPENAI_BASE_URL"))
        self.model = model

    async def evaluate(
        self,
        user_request: str,
        obis_url: str,
        response_json: Dict[str, Any],
        max_results_preview: int = 5
    ) -> Dict[str, Any]:
        """
        Uses LLM to judge if the OBIS response satisfies user intent.
        """

        preview = response_json.get("results", [])[:max_results_preview]
        summary = {
            "total": response_json.get("total", 0),
            "preview": preview
        }

        prompt = f"""
You are evaluating an AI biodiversity agent.

User request:
"{user_request}"

Generated OBIS URL:
{obis_url}

OBIS response summary:
{json.dumps(summary, indent=2)}

Task:
Determine whether the response satisfies the user's request.

Return JSON ONLY in this format:
{{
  "satisfied": true/false,
  "confidence": 0-1,
  "reason": "short explanation",
  "issues": ["issue1", "issue2"]
}}
"""

        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a strict evaluator for scientific data retrieval correctness."},
                {"role": "user", "content": prompt},
            ],
            temperature=0
        )

        content = resp.choices[0].message.content.strip()

        try:
            return json.loads(content)
        except Exception:
            return {
                "satisfied": False,
                "confidence": 0.0,
                "reason": "LLM returned invalid JSON",
                "issues": ["Invalid LLM output format"],
                "raw_output": content
            }


# =========================
# High-level helper
# =========================

async def full_validation_pipeline(
    request: str,
    params: Dict[str, Any],
    url: str,
    response_json: Dict[str, Any],
    endpoint: str,
    use_llm: bool = True,
) -> Dict[str, Any]:
    """
    Combined rule + LLM validation pipeline.
    """

    rule_validation = validate_obis_result(
        request=request,
        params=params,
        url=url,
        response_json=response_json,
        endpoint=endpoint
    )

    llm_validation = None
    if use_llm:
        validator = LLMValidator()
        llm_validation = await validator.evaluate(
            user_request=request,
            obis_url=url,
            response_json=response_json
        )

    return {
        "rule_validation": rule_validation,
        "llm_validation": llm_validation
    }
