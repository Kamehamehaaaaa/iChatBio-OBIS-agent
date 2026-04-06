### get_occurrence

## Example 1 - When the request has a scientific name.

```
"Request": "Search for Egregia menziesii"
"Response": {
    "params": {
        "scientificname": "Egregia menziesii"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request includes a scientific name hence populated the params with scientificname"
}
```

## Example 2 - When the reqest specifies information in quotes.

```
"Request": "Scientific name \\"this is fake but use it anyway\\""
"Response": {
    "params": {
        "scientificname": "this is fake but use it anyway"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user places a search term in quotes, always use the full text that is quoted, do not break it."
}
```

## Example 3 - Searching for a scientific name of species with a data range.

```
"Request": "Search for Egregia menziesii from January 15 2020 to August 15 2024"
"Response": {
    "params": {
        "scientificname": "Egregia menziesii",
        "startdate": "2020-01-15",
        "enddate": "2024-08-15"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason": "the user specifies the scientific name and date ranges."
}
```

## Example 4 - When request doesn't have a scientific name but an infraOrder.

```
"Request": "Search for brachyura"
"Response": {
    "params": {
        "scientificname": "brachyura"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason": "I know with full confidence that brachyura is an infra order and scientific name can be populated with that field."
}
```

## Example 5 - When request doesn't have a scientific name but an common name.

```
"Request": "Search for fish"
"Response": {
    "params": {
        "commonname": "fish"
    },
    "unresolved_params": [
        "scientificname"
    ],
    "clarification_needed": False,
    "reason": "The user request specifies a common name and populated the params with it. The agent will resolve it to scientific name."
}
```

## Example 6 - When request specifies region.

```
"Request": "Search for brachyura from Pacific"
"Response": {
    "params": {
        "scientificname": "brachyura",
        "area": "Pacific"
    },
    "clarification_needed": False,
    "reason": "The user request specifies a infra order and a place or region (Pacific) hence I populated the response as expected."
}
```

## Example 7 - When request specifies institute.

```
"Request": "Search for crabs from CSIRO Australia"
"Response": {
    "params": {
        "scientificname": "brachyura",
        "institute": "CSIRO Australia"
    },
    "clarification_needed": False,
    "reason": "The user request specifies crab which have a infra order brachyura and a institute (CSIRO Australia) hence I populated the response as expected."
}
```

## Example 8 - When request specifies institute and area.

```
"Request": "Search for Egregia menziesii from CSIRO in Australia"
"Response": {
    "params": {
        "scientificname": "brachyura",
        "institute": "CSIRO Australia"
    },
    "clarification_needed": False,
    "reason": "The user request specifies Egregia menziesii which is a and a institute (CSIRO Australia) hence I populated the response as expected."
}
```

## Example 9 - When the request has a common name and institute.

```
"Request": "Search for dolphins from marine institute of australia"
"Response": {
    "params": {
        "scientificname": "Delphinidae",
        "institute": "Marine institute of Australia",
        "area": "Australia"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request includes a common name but from my knowledge I populated scienticName as Delphinidae and institute and area from query with confidence."
}
```

## Example 10 - When the request doesn't have a species common or scientific name.

```
"Request": "Get records from Marine Institute of Australia"
"Response": {
    "params": {
        "institute": "Marine institute of Australia",
        "area": "Australia"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request includes a institute and area from query hence filled with confidence."
}
```

## Example 11 - When the request doesn't have a species common or scientific name.

```
"Request": "Get all records from dataset with uuid efa02fe9-6b5b-4173-85e7-912f71921fe7"
"Response": {
    "params": {
        "datasetid": "efa02fe9-6b5b-4173-85e7-912f71921fe7",
        "size": 10000
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request includes a dataset uuid and specifies all records hence populated params with datasetid and size as 10000 (max limit of api)."
}
```

## Example 12 - When request specifies an occurrence uuid

```
"Request": "Get occurrence record with id 0000039c-74cd-4e37-9bf8-848d560bf519 from australia from January 2020"
"Response": {
    "params": {
        "id": "0000039c-74cd-4e37-9bf8-848d560bf519"
    },
    "unresolved_params":null,
    "clarification_needed": False,
    "reason": "User request specifies an occurrence unique id, hence populated with id and ignored all other params."
}
```

## Example 5 - When the request specifies depth.

```
"Request": "occurrences records for species below 100 meters sea level"
"Response": {
    "params": {
        "startdepth": "100",
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request's for species below 100 meters hence populated startdepth with it."
}
```

### facet

## Example 1 - When the request has a scientific name.

```
"Request": "how many occurrence records there are for each species in the pacific region."
"Response": {
    "params": {
        "facets": ["originalScientificName"],
        "area": "Pacific"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request includes a scientific name hence populated the params with scientificname"
}
```

## Example 2 — Single Facet (Scientific Name Present)

```
"Request": "How many records are there per dataset for Egregia menziesii?"
"Response": {
    "params": {
        "facets": ["datasetID"],
        "scientificname": "Egregia menziesii"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason": "User requests categorical count grouped by dataset for a specific species, so datasetID facet is used."
}
```

## Example 3 — Geographic Filter + Facet

```
"Request": "How many records are there per institution in Australia for brachyura?"
"Response": {
    "params": {
        "facets": ["institutionCode"],
        "scientificname": "brachyura",
        "area": "Australia"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason": "User wants categorical breakdown by institution with geographic constraint, so institutionCode facet is used."
}
```

## Example 4 — Multiple Facets (Composite Required)

```
"Request": "Show record counts grouped by dataset and institution for kelp records."
"Response": {
    "params": {
        "facets": ["datasetID", "institutionCode"],
        "composite": True,
        "commonname": "kelp"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason": "User requests multi-level grouped breakdown by dataset and institution, so composite aggregation is required."
}
```

## Example 5 — Time-Based Categorical Breakdown

```
"Request": "How many records per year for Egregia menziesii?"
"Response": {
    "params": {
        "facets": ["date_year"],
        "scientificname": "Egregia menziesii"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason": "User requests categorical counts grouped by year, so date_year facet is used."
}
```

## Example 6 — Area Only, No Taxon
```
"Request": "How many records exist per family in the Indian Ocean?"
"Response": {
    "params": {
        "facets": ["family"],
        "area": "Indian Ocean"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason": "User requests categorical breakdown by taxonomic family within a geographic region."
}
```

## Example 7 — Depth Filter + Facet

```
"Request": "How many records per genus between 0 and 200 meters depth?"
"Response": {
    "params": {
        "facets": ["genus"],
        "startdepth": 0,
        "enddepth": 200
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason": "User requests categorical breakdown by genus constrained by depth range."
}
```

## Example 8 — Dataset Filter + Facet


```
"Request": "How many records per species in dataset aac5ca81-638a-4335-9aa7-5c2bda67a362?"
"Response": {
    "params": {
        "facets": ["species"],
        "datasetid": "aac5ca81-638a-4335-9aa7-5c2bda67a362"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason": "User specifies dataset UUID and wants categorical breakdown by species."
}
```

## Example 9 — Multi-Dimensional Time + Taxon (Composite)


```
"Request": "Show counts by year and family for brachyura in the Pacific."
"Response": {
    "params": {
        "facets": ["date_year", "family"],
        "composite": True,
        "scientificname": "brachyura",
        "area": "Pacific"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason": "User requests grouped breakdown across two categorical fields, so composite aggregation is required."
}
```

## Example 10 — Flags Filtering

```
"Request": "How many records per dataset excluding records flagged as ON_LAND?"
"Response": {
    "params": {
        "facets": ["datasetID"],
        "exclude": "ON_LAND"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason": "User requests dataset-level categorical counts while excluding specific quality flag."
}
```


### dataset

## Example 1 - When the request has a scientific name

```
"Request": "Get the datasets which have information about brachyura"
"Response": {
    "params": {
        "scientificname": "brachyura"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request includes a scientific name hence populated the params with scientificname"
}
```

## Example 2 - When the request has a area, region or place specified

```
"Request": "Get the datasets which have information about brachyura from Pacific region"
"Response": {
    "params": {
        "scientificname": "brachyura",
        "area": "Pacific"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request includes a scientific name and a region hence populated the params with scientificname and area"
}
```

## Example 3 - When the request has a institute specified.

```
"Request": "Get the datasets which have records from National Oceanic and Atmospheric Administration institute"
"Response": {
    "params": {
        "institute": "National Oceanic and Atmospheric Administration"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request includes a institute name hence populated the params with institute."
}
```

## Example 4 - Searching for a scientific name of species with a data range.

```
"Request": "Search for Egregia menziesii from January 15 2020 to August 15 2024"
"Response": {
    "params": {
        "scientificname": "Egregia menziesii",
        "startdate": "2020-01-15",
        "enddate": "2024-08-15"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason": "the user specifies the scientific name and date ranges."
}
```

## Example 5 - When the request specifies depth.

```
"Request": "datasets which have records for species below 100 meters sea level"
"Response": {
    "params": {
        "startdepth": "100",
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request's for species below 100 meters hence populated startdepth with it."
}
```

### institute

## Example 1 - When the request has a scientific name

```
"Request": "Get the institutes which have information about brachyura"
"Response": {
    "params": {
        "scientificname": "brachyura"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request includes a scientific name hence populated the params with scientificname"
}
```

## Example 2 - When the request has a area, region or place specified

```
"Request": "Get the institutes which have information about brachyura from Pacific region"
"Response": {
    "params": {
        "scientificname": "brachyura",
        "area": "Pacific"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request includes a scientific name and a region hence populated the params with scientificname and area"
}
```

## Example 3 - When the request has a institute specified.

```
"Request": "Get the institutes which have records from dataset UUID efa02fe9-6b5b-4173-85e7-912f71921fe7"
"Response": {
    "params": {
        "datasetid": "efa02fe9-6b5b-4173-85e7-912f71921fe7"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request includes a institute name hence populated the params with institute."
}
```

## Example 4 - Searching for a scientific name of species with a data range.

```
"Request": "retrive institutes which have records for Egregia menziesii from January 15 2020 to August 15 2024"
"Response": {
    "params": {
        "scientificname": "Egregia menziesii",
        "startdate": "2020-01-15",
        "enddate": "2024-08-15"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason": "the user specifies the scientific name and date ranges."
}
```

## Example 5 - When the request specifies depth.

```
"Request": "institutes which have records for species below 100 meters sea level"
"Response": {
    "params": {
        "startdepth": "100",
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request's for species below 100 meters hence populated startdepth with it."
}
```

### dataset_lookup

## Example 1 - When the request has a dataset uuid.

```
"Request": "Get the information for dataset with UUID efa02fe9-6b5b-4173-85e7-912f71921fe7"
"Response": {
    "params": {
        "id": "efa02fe9-6b5b-4173-85e7-912f71921fe7"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request specified a dataset uuid hence populated the params with it."
}
```

## Example 2 - When the request doesnt have UUID.

```
"Request": "Get the information for Australian dataset"
"Response": {
    "params": {},
    "unresolved_params": ["id"],
    "clarification_needed": True,
    "reason" : "The user request doesn;t have UUID which is required."
}
```

### dataset_search

## Example 1 - When the request asks for location based.

```
"Request": "Get the information for Australian dataset"
"Response": {
    "params": {
        "queryContent": "Australia"
    },
    "unresolved_params": ["id"],
    "clarification_needed": False,
    "reason" : "The user request asks for dataset in Australia hence populated query content with that."
}
```

## Example 2 - When the request has come query content like contributor name.

```
"Request": "Datasets contributed by John Doe"
"Response": {
    "params": {
        "queryContent": "John Doe"
    },
    "unresolved_params": ["id"],
    "clarification_needed": False,
    "reason" : "The user request asks for dataset contributed by John Doe hence populated query content with that."
}
```


### institute_lookup

## Example 1 - When the request has a institute id.

```
"Request": "Get the information for institute with id 19482"
"Response": {
    "params": {
        "id": "19482"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request specified a institute id hence populated the params with it."
}
```

## Example 2 - When the request specify institute name or area.

```
"Request": "Get information for Wildlife institute of India"
"Response": {
    "params": {
        "institute": "Wildlife institute of India",
        "area": "India"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request specifies institute name and area hence populated it."
}
```

### taxon

## Example 1 - When the request has a common name.

```
"Request": "Show me the taxonomy for Atlantic cod."
"Response": {
    "params": {
        "commonname": "Atlantic cod",
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request specifies a common name hence populated it."
}
```

## Example 2 - When the request has a scientific name.

```
"Request": "list species in family brachyura"
"Response": {
    "params": {
        "scientificname": "brachyura"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request includes a scientific name hence populated the params with scientificname"
}
```


### checklist

## Example 1 - When the request has a scientific name.

```
"Request": "Search for Egregia menziesii"
"Response": {
    "params": {
        "scientificname": "Egregia menziesii"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request includes a scientific name hence populated the params with scientificname"
}
```

## Example 2 - When the reqest specifies information in quotes.

```
"Request": "Scientific name \\"this is fake but use it anyway\\""
"Response": {
    "params": {
        "scientificname": "this is fake but use it anyway"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user places a search term in quotes, always use the full text that is quoted, do not break it."
}
```

## Example 3 - Searching for a scientific name of species with a data range.

```
"Request": "Search for Egregia menziesii from January 15 2020 to August 15 2024"
"Response": {
    "params": {
        "scientificname": "Egregia menziesii",
        "startdate": "2020-01-15",
        "enddate": "2024-08-15"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason": "the user specifies the scientific name and date ranges."
}
```

## Example 4 - When request doesn't have a scientific name but an infraOrder.

```
"Request": "Search for brachyura"
"Response": {
    "params": {
        "scientificname": "brachyura"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason": "I know with full confidence that brachyura is an infra order and scientific name can be populated with that field."
}
```

## Example 5 - When request doesn't have a scientific name but an common name.

```
"Request": "Search for fish"
"Response": {
    "params": {
        "commonname": "fish"
    },
    "unresolved_params": [
        "scientificname"
    ],
    "clarification_needed": False,
    "reason": "The user request specifies a common name and populated the params with it. The agent will resolve it to scientific name."
}
```

## Example 6 - When request specifies region.

```
"Request": "Search for brachyura from Pacific"
"Response": {
    "params": {
        "scientificname": "brachyura",
        "area": "Pacific"
    },
    "clarification_needed": False,
    "reason": "The user request specifies a infra order and a place or region (Pacific) hence I populated the response as expected."
}
```

## Example 7 - When request specifies institute.

```
"Request": "Search for crabs from CSIRO Australia"
"Response": {
    "params": {
        "scientificname": "brachyura",
        "institute": "CSIRO Australia"
    },
    "clarification_needed": False,
    "reason": "The user request specifies crab which have a infra order brachyura and a institute (CSIRO Australia) hence I populated the response as expected."
}
```

## Example 8 - When request specifies institute and area.

```
"Request": "Search for Egregia menziesii from CSIRO in Australia"
"Response": {
    "params": {
        "scientificname": "brachyura",
        "institute": "CSIRO Australia"
    },
    "clarification_needed": False,
    "reason": "The user request specifies Egregia menziesii which is a and a institute (CSIRO Australia) hence I populated the response as expected."
}
```

## Example 9 - When the request has a common name and institute.

```
"Request": "Search for dolphins from marine institute of australia"
"Response": {
    "params": {
        "scientificname": "Delphinidae",
        "institute": "Marine institute of Australia",
        "area": "Australia"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request includes a common name but from my knowledge I populated scienticName as Delphinidae and institute and area from query with confidence."
}
```

## Example 10 - When the request specifies depth.

```
"Request": "Search for species below 100 meters"
"Response": {
    "params": {
        "startdepth": "100",
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request's for species below 100 meters hence populated startdepth with it."
}
```