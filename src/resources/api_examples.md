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
    "params": null,
    "unresolved_params": [
        "scientificname"
    ],
    "clarification_needed": True,
    "reason": "The user request specifies a common name and I'm not aware of the scientific name of the species."
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


### facet

## Example 1 - When the request has a scientific name.

```
"Request": "how many occurrence records there are for each species in the pacific region."
"Response": {
    "params": {
        "facets": "originalScientificName",
        "areaid": "Pacific"
    },
    "unresolved_params": null,
    "clarification_needed": False,
    "reason" : "The user request includes a scientific name hence populated the params with scientificname"
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