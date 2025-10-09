import importlib
import os
import yaml
from urllib.parse import urlencode
import requests
from utils import utils
import json

def build_system_prompt(api):
    SYSTEM_PROMPT_TEMPLATE = """
        {system_prompt}

        # Examples

        {examples_doc}
    """

    system_prompt = importlib.resources.files().joinpath("../resources/system_prompt.md").read_text()
    examples_doc = get_api_examples("src/resources/api_examples.md", api)

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        api=api,
        system_prompt=system_prompt,
        examples_doc=examples_doc,
    ).strip()

    print(prompt)

    return prompt

def get_api_examples(file_path: str, api_name: str) -> str:
    with open(file_path, "r") as f:
        content = f.read()

    # Find the section header for the API
    marker = f"### {api_name}"
    parts = content.split(marker)

    if len(parts) < 2:
        return f"No examples found for {api_name}"

    # Take content after the marker until next section
    section = parts[1]
    section = section.split("### ", 1)[0].strip()

    return f"{section}"