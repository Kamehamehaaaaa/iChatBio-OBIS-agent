import os
import json
from utils import utils
import requests

def initializeAreaIds():
    areas = []

    url = utils.generate_obis_url('area', None)
    response = requests.get(url)

    if response.ok:
        results = response.json()['results']
        for i in results:
            areas.append({
                "id": i.get("id"),
                "name": i.get("name"),
                "type": i.get("type")
            })
    
    if len(areas) > 0:
        with open("areas.json", "w", encoding="utf-8") as f:
            json.dump(areas, f, indent=2, ensure_ascii=False)
    else:
        print("No areaids")
        
    return

def initializeInstitutes():
    institutes = []

    url = utils.generate_obis_url('institute', None)
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
    
def initializeDatasets():
    datasets = []

    url = utils.generate_obis_url('dataset', None)
    response = requests.get(url)

    if response.ok:
        results = response.json()['results']
        for i in results:
            if i["id"] == None:
                continue
            datasets.append(i)
    
    if len(datasets) > 0:
        with open("datasets.json", "w", encoding="utf-8") as f:
            json.dump(datasets, f, indent=2, ensure_ascii=False)
    else:
        print("No datasets")
        
    return

def getData(queryType):
    path = f"{queryType}.json"
    if os.path.exists(path) == False:
        match queryType:
            case "areas":
                initializeAreaIds()
            case "institutes":
                initializeInstitutes()
            case "datasets":
                initializeDatasets()
            case _:
                pass

    with open(path, "r") as f:
        entity = json.load(f)

    return entity