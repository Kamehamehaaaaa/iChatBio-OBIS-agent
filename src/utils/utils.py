import importlib
import os
import yaml
from urllib.parse import urlencode, quote
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
        extensionValue = quote(str(payload.pop(extensionParam)))
    else:
        extensionValue = 2024

    extensionValue = str(extensionValue)

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
    if best_matches[0].get("score", 0) < 0.5:
        return []
    return best_matches


async def getDatasetId(datasetname: str) -> str | list:
    query = {}
    query['q'] = datasetname
    query['size'] = 10
    query['skip'] = 0

    url = generate_obis_url('dataset/search2', query)
    response = requests.get(url)

    response_json = response.json()

    results = response_json.get("results", [])

    if len(results) > 0:
        return url, [[x.get('id', ''), x.get('title', '')] for x in results]

    return url, None


async def getScientificName(commonname: str) -> str | list:
    query = {}
    query['q'] = commonname
    query['size'] = 10
    query['skip'] = 0

    url = generate_obis_url('taxon/search/common', query)
    response = requests.get(url)

    response_json = response.json()

    results = response_json.get("results", [])

    print(results)

    if len(results) > 0:
        return url, [[x.get('commonName', ''), x.get('scientificName', '')] for x in results]

    return url, None

async def getTaxonIdFromScientificName(scientificname: str) -> list:
    query = {}
    query['q'] = scientificname
    query['size'] = 10
    query['skip'] = 0

    url = generate_obis_url('taxon/search', query)
    response = requests.get(url)

    response_json = response.json()

    results = response_json.get("results", [])

    if len(results) > 0:
        return [[x.get('taxonID', ''), x.get('scientificName', '')] for x in results]

    return []

async def resolveCommonName(commonname: str) -> str | list:
    query = {}
    query['q'] = commonname
    query['size'] = 10
    query['skip'] = 0

    url = generate_obis_url('taxon/search/common', query)
    response = requests.get(url)

    response_json = response.json()

    results = response_json.get("results", [])

    if len(results) > 0:
        return url, [[x.get('commonName', ''), x.get('taxonID', ''), x.get('scientificName', '')] for x in results]

    return url, None


async def resolveParams(params: dict, parameter: str, resolveToParam: str, process):
    try:
        match parameter:
            case "commonname":
                url, solution = await resolveCommonName(params.get("commonname"))
 
                if solution == None or len(solution) == 0:
                    await exceptionHandler(process, None, f"Not able to resolve {params.get("commonname")} to a scientific name or taxonID")
                    return False
                
                if len(solution) > 1:
                    # await utils.exceptionHandler(process, None, "Multiple scientific names found for the given species")
                    content = "Multiple scientific name matches found for "+str(solution[0][0])+" : \n " + str(solution[0][2]) + " with taxonID " +str(solution[0][1])
                    for i in solution[1:(min(5, len(solution)))]:
                        content += "\n"
                        content += str(i[2]) + " with taxonID " + str(i[1])
                    content += "\n"
                    content += f"Fetching records for {solution[0][2]}"
                    
                    await process.log(content)
                params[resolveToParam] = solution[0][1]
                del params['commonname']
                return True
            
            case "datasetname":
                datasetFetchUrl, datasets = await getDatasetId(params.get("datasetname"))

                if not datasets or len(datasets) == 0:
                    await exceptionHandler(process, None, "The dataset specified doesn't match any OBIS list of datasets")
                    return False
                
                if len(datasets) > 1:
                    # exceptionHandler(process, None, "Multiple datasets found for the given query")
                    content = "Multiple datasets matches found: " + datasets[0][1]
                    for i in datasets[1:]:
                        content += ", "
                        content += i[1]

                    await process.log(content)

                    # await process.create_artifact(
                    #     mimetype="application/json",
                    #     description="multiple dataset matches found for the given query",
                    #     uris=[datasetFetchUrl],
                    #     metadata={
                    #         "data_source": "OBIS",
                    #         "portal_url": "portal_url",
                    #     }, 
                    #     content=content
                    # )
                    # return False

                params[resolveToParam] = datasets[0][0]
                del params['datasetname']
                return True
            
            case "institute":
                institutes = await getInstituteId(params)
                if not institutes or len(institutes) == 0:
                    await process.log("OBIS doesn't have any institutes named " + params["institute"])
                    return False
                
                if institutes[0].get("score") < 0.80:
                    institute = ""+institutes[0].get("name", "")
                    if len(institutes) > 1:
                        for i in institutes[1:]:
                            institute += ", " + i.get("name", "")
                        ret_log = "OBIS has " + str(len(institutes)) + " closest matching institute names with the input. " + \
                                                "They are " + institute + ". Records for " + institutes[0].get("name", "") + \
                                                " will be fetched"
                        await process.log(ret_log)
                params[resolveToParam] = institutes[0].get("id", "")
                del params["institute"]
                if "area" in params:
                    del params["area"]
                return True
            
            case "area":
                matches = await getAreaId(params.get("area"))
                # print("area matches")
                # print(matches)
                if not matches or len(matches) == 0:
                    await exceptionHandler(process, None, "The area specified doesn't match any OBIS list of areas")
                    return False
                if len(matches) > 1:
                    await process.log("Multiple area matches found")
                areas = ""+matches[0].get("areaid")
                for match in matches[1:]:
                    areas+=","
                    areas+=match.get("areaid")
                params[resolveToParam] = areas
                del params["area"]
                return True
            
            case "scientificname":
                ids = await getTaxonIdFromScientificName(params.get('scientificname', ''))
                if not ids or len(ids) == 0:
                    await exceptionHandler(process, None, "not able to resolve scientific name to taxon id.")
                    return False
                params[resolveToParam] = ids[0][0]
                del params['scientificname']
                return True
            
            case _:
                raise ValueError()
            
    except ValueError as e:
        await exceptionHandler(process, None, "OBIS agent encountered an error with parameter resolution")
