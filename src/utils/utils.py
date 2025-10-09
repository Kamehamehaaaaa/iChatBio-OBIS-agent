import importlib
import os
import yaml
from urllib.parse import urlencode
import json
import requests

from fuzzywuzzy import fuzz, process

def getValue(key):
    value = os.getenv(key)

    if value == None:
        with open('src/env.yaml', 'r') as file:
            data = yaml.safe_load(file)

        value = data[key]

    return value

def generate_obis_url(api, payload):
    obis_url = "https://api.obis.org/"
    if api == "facet":
        tmp = payload["facets"]
        facets = tmp[0]
        for i in tmp[1:]:
            facets = facets + "," + i
        payload["facets"] = facets
    if payload == None or len(payload) == 0:
        return obis_url+api
    params = urlencode(payload)
    url = obis_url+api+'?'+params
    return url

def generate_obis_extension_url(api, payload, extensionParam, paramsRequired):
    if extensionParam in payload:
        extensionValue = payload.pop(extensionParam)
    else:
        extensionValue = 2024

    params = urlencode(payload)
    obis_url = "https://api.obis.org/"
    if paramsRequired:
        url = obis_url+api+"/"+extensionValue+'?'+params
    else:
        url = obis_url+api+"/"+extensionValue
    return url

def generate_mapper_obis_url(api, payload):
    params = urlencode(payload)
    obis_url = "https://mapper.obis.org/"
    url = obis_url+api+'?'+params
    return url

def initializeAreaIds():
    areas = []

    url = generate_obis_url('area', None)
    response = requests.get(url)

    if response.ok:
        results = response.json()['results']
        for i in results:
            areas.append({
                "areaid": i.get("id"),
                "name": i.get("name"),
                "type": i.get("type")
            })
    
    if len(areas) > 0:
        with open("areaids.json", "w", encoding="utf-8") as f:
            json.dump(areas, f, indent=2, ensure_ascii=False)
    else:
        print("No areaids")
        
    return

def initializeInstitutes():
    institutes = []

    url = generate_obis_url('institute', None)
    response = requests.get(url)

    if response.ok:
        results = response.json()['results']
        for i in results:
            if i["id"] == None:
                continue
            if i["country"] != None:
                i["name"] += " " + i["country"]
            institutes.append(i)
    
    if len(institutes) > 0:
        with open("institutes.json", "w", encoding="utf-8") as f:
            json.dump(institutes, f, indent=2, ensure_ascii=False)
    else:
        print("No institutes")
        
    return

def getData(path, queryType):
    if os.path.exists(path) == False:
        match queryType:
            case "areaid":
                initializeAreaIds()
            case "institute":
                initializeInstitutes()
            case _:
                pass

    with open(path, "r") as f:
        entity = json.load(f)

    return entity

def setup():
    pass


def destroy():
    paths = ["areaids.json", "institutes.json"]
    for path in paths:
        if os.path.exists(path):
            os.remove(path)
            print(f"{path} deleted successfully.")

async def getAreaId(query):
    areas = getData("areaids.json", "areaid")
    
    query = query.lower()
    matches = [
        area for area in areas
        if query in area["name"].lower() or query in area["areaid"].lower()
    ]

    return matches

async def getInstituteId(query):
    institutes = getData("institutes.json", "institute")

    query_dict = {"name": query.get("institute").lower()}

    if "area" in query:
        query_dict["name"] = query_dict.get("name") + " " + query.get("area").lower()

    match, score = process.extractOne(query=query_dict, choices=institutes, processor=lambda d:d["name"], scorer=fuzz.ratio)

    print(match, score)
    if score > 60:
        return [match]
    else:
        return [-1]
