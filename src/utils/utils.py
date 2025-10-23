import importlib
import os
import yaml
from urllib.parse import urlencode
import json
import requests

# from fuzzywuzzy import fuzz, process
from rapidfuzz import fuzz, process
from sentence_transformers import SentenceTransformer, util
import torch
import numpy as np

def getValue(key):
    value = os.getenv(key)

    if value == None:
        with open('src/env.yaml', 'r') as file:
            data = yaml.safe_load(file)

        value = data[key]

    return value

def generate_obis_url(api, payload):
    obis_url = "https://api.obis.org/"
    # payload = payload["params"]
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
        extensionValue = str(payload.pop(extensionParam))
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

    query_dict = {"name": query.get("institute")}

    if "area" in query:
        query_dict["name"] = query_dict.get("name") + " " + query.get("area")

    # match, score = process.extract(query=query_dict, choices=institutes, processor=lambda d:d["name"], scorer=fuzz.token_set_ratio)

    matches = await hybrid_match(query=query_dict, institutes=institutes)
    # print(matches)
    return matches

# function to get best match
async def fn(query, choice):
    if choice == None:
        return 0
    q_tokens = query.split(' ')
    c_tokens = choice.split(' ')
    ret = 0

    for i in q_tokens:
        if i in c_tokens:
            ret+=1

    if ret > 0:
        print(choice)
    
    return ret


async def exceptionHandler(p, e, descr):
    if e != None:
        await p.log(str(e) +" "+ descr)
    else:
        await p.log(descr)
    return


async def hybrid_match(query, institutes, best_n = 5):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    names = [i["name"] for i in institutes]
    query_token_len = float(len(query["name"].split(" ")))
    
    # Embedding scores
    q_emb = model.encode(query["name"], convert_to_tensor=True)
    inst_embs = model.encode(names, convert_to_tensor=True)
    emb_scores = util.cos_sim(q_emb, inst_embs)[0].cpu().numpy()

    # Fuzzy scores
    fuzzy_scores = []
    for n in names:
        tp = ( await fn(query["name"], n)) / query_token_len
        fuzzy_scores.append(tp)
    
    fuzzy_scores = np.array(fuzzy_scores)

    # Weighted combination (50% semantic, 50% fuzzy)
    hybrid_scores = 0.5 * emb_scores + 0.5 * fuzzy_scores

    best_ind = np.argsort(hybrid_scores)[::-1][:best_n]
    best_matches = [
        {
            "id": institutes[i]["id"],
            "name": institutes[i]["name"],
            "score": float(hybrid_scores[i])
        }
        for i in best_ind
    ]
    return best_matches
