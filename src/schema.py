from pydantic import BaseModel, field_validator, Field, constr, conint
from typing import Optional, Annotated, Literal, Required, List
from datetime import datetime
from enum import Enum

class AnalyzeRequestResponse(BaseModel):
    entrypoints: List[str] = Field(None, description="entrypoint that needs to be called to complete the user request. The entrypoint should be from the availbale list of entrypoints.")
    next: Optional[str] = Field(None, description="after calling the entrypoint and getting its data, what next step should be taken to complete the user request. If you are not sure about this do not populate this feild.")
    summary: Optional[str] = Field(None, description="use this to summarize why you chose this endpoint and what should be done next.")

class occurrenceApi(BaseModel):

    scientificname: Optional[str] = Field(None, 
                                          description="Scientific name. Leave empty to include all taxa. Can be used to include infra order of species if specified in the request.", 
                                          examples=["Delphinus delphis", "Alosa pseudoharengus", "Brachyura"])
    taxonid: Optional[str] = Field(None, description="Taxon AphiaID.")
    datasetid: Optional[str] = Field(None, description="Dataset UUID.")
    areaid: Optional[str] = Field(None, description="Area ID. the OBIS area identifier. Its not the name of the place, area or region.")
    instituteid: Optional[str] = Field(None, description="Institute ID. the OBIS institute identifier. It is not the name of the institute.")
    nodeid: Optional[str] = Field(None, description="Node UUID. the OBIS node identifier")
    
    startdate: Optional[str] = Field(None, description="Start date formatted as YYYY-MM-DD. Fetch records after this date.")
    enddate: Optional[str] = Field(None, description="End date formatted as YYYY-MM-DD.")
    
    startdepth: Optional[int] = Field(None, description="Start depth, in meters.")
    enddepth: Optional[int] = Field(None, description="End depth, in meters.")
    
    geometry: Optional[str] = Field(None, description="Geometry, formatted as WKT or GeoHash.")
    
    redlist: Optional[bool] = Field(None, description="Red List species only, true/false.")
    hab: Optional[bool] = Field(None, description="HAB species only, true/false.")
    wrims: Optional[bool] = Field(None, description="WRiMS species only, true/false.")
    mof: Optional[bool] = Field(None, description="Include MeasurementOrFact records, true/false.")
    dna: Optional[bool] = Field(None, description="Include DNADerivedData records, true/false.")
    
    extensions: Optional[str] = Field(None, description="Extensions to include (e.g. MeasurementOrFact, DNADerivedData).")
    hasextensions: Optional[str] = Field(None, description="Extensions that need to be present (e.g. MeasurementOrFact, DNADerivedData).")
    
    qcfields: Optional[bool] = Field(None, description="Include lists of missing and invalid fields, true/false.")
    dropped: Optional[str] = Field(None, description="Include dropped records (include) or get dropped records exclusively (true).")
    absence: Optional[str] = Field(None, description="Include absence records (include) or get absence records exclusively (true).")
    event: Optional[str] = Field(None, description="Include pure event records (include) or get pure event records exclusively (true).")
    
    flags: Optional[str] = Field(None, description="Comma separated list of quality flags which need to be set.")
    exclude: Optional[str] = Field(None, description="Comma separated list of quality flags to be excluded.")
    
    fields: Optional[str] = Field(None, description="Fields to be included in the result set.")
    after: Optional[str] = Field(None, description="Occurrence UUID up to which to skip.")
    size: Optional[int] = Field(None, description="Response size. Maximum value is 10000.")
    
    measurementtype: Optional[str] = Field(None, description="Measurement type to be present for occurrence.")
    measurementtypeid: Optional[str] = Field(None, description="Measurement type ID to be present for occurrence.")
    measurementvalue: Optional[str] = Field(None, description="Measurement value to be present for occurrence.")
    measurementvalueid: Optional[str] = Field(None, description="Measurement value ID to be present for occurrence.")
    measurementunit: Optional[str] = Field(None, description="Measurement unit to be present for occurrence.")
    measurementunitid: Optional[str] = Field(None, description="Measurement unit ID to be present for occurrence.")

    id: Optional[str] = Field(None, description="Used to fetch individual occurrence records. When this is populated ignore all other params.")

    #extra parameters which are not mentioned in api documentation. 
    area: Optional[str] = Field(None, description="Name of the Area, place or region specified in the user request.")
    institute: Optional[str] = Field(None, description="Name of the institute in the request.")
    datasetname: Optional[str] = Field(None, description="name of the dataset specified in the query")
    commonname: Optional[str] = Field(None, description="Common name passed in the user query")

    @field_validator('startdate', 'enddate')
    def validate_date_format(cls, value):
        allowed_formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]
        for format in allowed_formats:
            try:
                dt = datetime.strptime(value, format)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError("Incorrect date format. Allowed formats: YYYY-MM-DD, YYYY/MM/DD, DD-MM-YYYY, DD/MM/YYYY")

    @field_validator('size')
    def validate_size(cls,value):
        return min(10000, value)


class datasetApi(BaseModel):

    scientificname: Optional[str] = Field(None, 
                                          description="Scientific name. Leave empty to include all taxa. Can be used to include infra order of species if specified in the request.", 
                                          examples=["Delphinus delphis", "Alosa pseudoharengus", "Brachyura"])
    taxonid: Optional[str] = Field(None, description="Taxon AphiaID.")
    areaid: Optional[str] = Field(None, description="Area ID. the OBIS area identifier. Its not the name of the place, area or region.")
    instituteid: Optional[str] = Field(None, description="Institute ID. the OBIS institute identifier. It is not the name of the institute.")
    nodeid: Optional[str] = Field(None, description="Node UUID. the OBIS node identifier")
    
    startdate: Optional[str] = Field(None, description="Start date formatted as YYYY-MM-DD. Fetch records after this date.")
    enddate: Optional[str] = Field(None, description="End date formatted as YYYY-MM-DD.")
    
    startdepth: Optional[int] = Field(None, description="Start depth, in meters.")
    enddepth: Optional[int] = Field(None, description="End depth, in meters.")
    
    geometry: Optional[str] = Field(None, description="Geometry, formatted as WKT or GeoHash.")
    
    redlist: Optional[bool] = Field(None, description="Red List species only, true/false.")
    hab: Optional[bool] = Field(None, description="HAB species only, true/false.")
    wrims: Optional[bool] = Field(None, description="WRiMS species only, true/false.")
    
    dropped: Optional[str] = Field(None, description="Include dropped records (include) or get dropped records exclusively (true).")
    absence: Optional[str] = Field(None, description="Include absence records (include) or get absence records exclusively (true).")
    exclude: Optional[str] = Field(None, description="Comma separated list of quality flags to be excluded.")
    
    fields: Optional[str] = Field(None, description="Fields to be included in the result set.")
    after: Optional[str] = Field(None, description="Occurrence UUID up to which to skip.")
    size: Optional[int] = Field(None, description="Response size.")
    
    #extra parameters which are not mentioned in api documentation. 
    area: Optional[str] = Field(None, description="Name of the Area, place or region specified in the user request.")
    institute: Optional[str] = Field(None, description="Name of the institute in the request.")
    datasetname: Optional[str] = Field(None, description="name of the dataset specified in the query")
    commonname: Optional[str] = Field(None, description="common name of the species specified in the query")

    @field_validator('startdate', 'enddate')
    def validate_date_format(cls, value):
        allowed_formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]
        for format in allowed_formats:
            try:
                dt = datetime.strptime(value, format)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError("Incorrect date format. Allowed formats: YYYY-MM-DD, YYYY/MM/DD, DD-MM-YYYY, DD/MM/YYYY")
    
class datasetLookupApi(BaseModel):
    id: str = Field(None, description="dataset uuid from the request.",
                              examples=["00000002-3cef-4bc1-8540-2c20b4798855"])
    datasetname: Optional[str] = Field(None, description="name of the dataset specified in the query")
    
class instituteLookupApi(BaseModel):
    id: Optional[str] = Field(None, description="institute id",
                              examples=["19482"])
    #extra parameters which are not mentioned in api documentation. 
    area: Optional[str] = Field(None, description="Name of the Area, place or region specified in the user request.")
    institute: Optional[str] = Field(None, description="Name of the institute in the request.")

class occurrenceLookupApi(BaseModel):
    id: Optional[str] = Field(None, description="occurrence record id",
                              examples=["00000002-3cef-4bc1-8540-2c20b4798855"])

class FacetField(str, Enum):
    basisOfRecord = "basisOfRecord"
    class_ = "class"
    classid = "classid"
    collectionCode = "collectionCode"
    coordinateUncertaintyInMeters = "coordinateUncertaintyInMeters"
    dataGeneralizations = "dataGeneralizations"
    datasetID = "datasetID"
    datasetName = "datasetName"
    date_end = "date_end"
    date_mid = "date_mid"
    date_start = "date_start"
    date_year = "date_year"
    decimalLatitude = "decimalLatitude"
    decimalLongitude = "decimalLongitude"
    eventDate = "eventDate"
    eventID = "eventID"
    eventType = "eventType"
    family = "family"
    familyid = "familyid"
    genus = "genus"
    genusid = "genusid"
    geodeticDatum = "geodeticDatum"
    infraphylum = "infraphylum"
    infraphylumid = "infraphylumid"
    institutionCode = "institutionCode"
    kingdom = "kingdom"
    kingdomid = "kingdomid"
    license = "license"
    locationRemarks = "locationRemarks"
    marine = "marine"
    maximumElevationInMeters = "maximumElevationInMeters"
    megaclass = "megaclass"
    megaclassid = "megaclassid"
    minimumElevationInMeters = "minimumElevationInMeters"
    occurrenceID = "occurrenceID"
    occurrenceStatus = "occurrenceStatus"
    order = "order"
    orderid = "orderid"
    organismID = "organismID"
    organismName = "organismName"
    parentEventID = "parentEventID"
    phylum = "phylum"
    phylumid = "phylumid"
    rightsHolder = "rightsHolder"
    samplingProtocol = "samplingProtocol"
    scientificName = "scientificName"
    scientificNameID = "scientificNameID"
    sex = "sex"
    species = "species"
    speciesid = "speciesid"
    subphylum = "subphylum"
    subphylumid = "subphylumid"
    superclass = "superclass"
    superclassid = "superclassid"
    type_ = "type"
    id_ = "id"
    dataset_id = "dataset_id"
    node_id = "node_id"
    dropped = "dropped"
    absence = "absence"
    originalScientificName = "originalScientificName"
    aphiaID = "aphiaID"
    flags = "flags"
    bathymetry = "bathymetry"
    shoredistance = "shoredistance"

class facetsAPIParams(BaseModel):
    facets: List[FacetField] = Field(None, description="Comma separated list of facets. List of facet fields to aggregate on", examples= ["originalScientificName,flags", "node_id"])
    composite: Optional[bool] = Field(None, description="""
        If true, performs multi-level (nested) aggregation across multiple facet fields.
        Returns counts grouped by combinations of facet values rather than independent counts per facet.
        Requires two or more facets.
    """)
    scientificname: Optional[str] = Field(None, description="Scientific name. Leave empty to include all taxa", examples=["brachyura", "Cancer borealis"])
    taxonid: Optional[str] = Field(None, description="Taxon AphiaID")
    areaid: Optional[str] = Field(None, description="Area ID")
    datasetid: Optional[str] = Field(None, description="Dataset UUID")
    nodeid: Optional[str] = Field(None, description="Node UUID")
    startdate: Optional[str] = Field(None, description="Start date formatted as YYYY-MM-DD")
    enddate: Optional[str] = Field(None, description="End date formatted as YYYY-MM-DD")
    startdepth: Optional[int] = Field(None, ge=0, description="Start depth in meters")
    enddepth: Optional[int] = Field(None, ge=0, description="End depth in meters")
    geometry: Optional[str] = Field(None, description="Geometry, formatted as WKT or GeoHash", examples=["POLYGON((140 -40, 150 -40, 150 -30, 140 -30, 140 -40))"])
    redlist: Optional[bool] = Field(None, description="Red List species only")
    hab: Optional[bool] = Field(None, description="HAB species only")
    wrims: Optional[bool] = Field(None, description="WRiMS species only")
    dropped: Optional[str] = Field(None, description="Include dropped records (include) or only dropped (true)")
    absence: Optional[str] = Field(None, description="Include absence records (include) or only absence (true)")
    flags: Optional[str] = Field(None, description="Comma separated list of quality flags which need to be set")
    exclude: Optional[str] = Field(None, description="Comma separated list of quality flags to be excluded")

    area: Optional[str] = Field(None, description="Name of the Area, place or region specified in the user request.")
    institute: Optional[str] = Field(None, description="Name of the institute in the request.")
    datasetname: Optional[str] = Field(None, description="name of the dataset specified in the query")
    commonname: Optional[str] = Field(None, description="Common name passed in the user query")

    @field_validator('startdate', 'enddate')
    def validate_date_format(cls, value):
        if value is None:
            return value
        allowed_formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]
        for fmt in allowed_formats:
            try:
                dt = datetime.strptime(value, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError("Incorrect date format. Allowed: YYYY-MM-DD, YYYY/MM/DD, DD-MM-YYYY, DD/MM/YYYY")

    @field_validator('enddepth')
    def validate_depth_range(cls, value, values):
        start_depth = values.get('startdepth')
        if start_depth is not None and value is not None and value < start_depth:
            raise ValueError("enddepth must be greater than or equal to startdepth")
        return value
    
    @field_validator('facets', mode="before")
    def normalize_facets(cls, value):
        if value is None:
            return []
        
        if isinstance(value, str):
            value = [v.strip() for v in value.split(',')]
        
        return value
    
    @field_validator("composite")
    def validate_composite_logic(cls, value, info):
        if value:
            facets = info.data.get("facets")
            if not facets or len(facets) < 2:
                raise ValueError("Composite aggregation requires at least two facets.")
        return value

class instituteApi(BaseModel):
    scientificname: Optional[str] = Field(
        None, description="Scientific name. Leave empty to include all taxa."
    )
    taxonid: Optional[str] = Field(
        None, description="Taxon AphiaID."
    )
    areaid: Optional[str] = Field(
        None, description="Area ID."
    )
    datasetid: Optional[str] = Field(
        None, description="Dataset UUID."
    )
    nodeid: Optional[str] = Field(
        None, description="Node UUID."
    )
    startdate: Optional[str] = Field(
        None, description="Start date formatted as YYYY-MM-DD."
    )
    enddate: Optional[str] = Field(
        None, description="End date formatted as YYYY-MM-DD."
    )
    startdepth: Optional[int] = Field(
        None, description="Start depth, in meters."
    )
    enddepth: Optional[int] = Field(
        None, description="End depth, in meters."
    )
    geometry: Optional[str] = Field(
        None, description="Geometry, formatted as WKT or GeoHash."
    )
    redlist: Optional[bool] = Field(
        None, description="Red List species only, true/false."
    )
    hab: Optional[bool] = Field(
        None, description="HAB species only, true/false."
    )
    wrims: Optional[bool] = Field(
        None, description="WRiMS species only, true/false."
    )
    flags: Optional[str] = Field(
        None, description="Comma separated list of quality flags which need to be set."
    )
    exclude: Optional[str] = Field(
        None, description="Comma separated list of quality flags to be excluded."
    )
    dropped: Optional[str] = Field(
        None, description="Include dropped records (include) or get dropped records exclusively (true)."
    )
    absence: Optional[str] = Field(
        None, description="Include absence records (include) or get absence records exclusively (true)."
    )

    #extra parameters which are not mentioned in api documentation. 
    area: Optional[str] = Field(None, description="Name of the Area, place or region specified in the user request.")
    institute: Optional[str] = Field(None, description="Name of the institute in the request.")
    commonname: Optional[str] = Field(None, description="Common name passed in the user query")

    @field_validator('startdate', 'enddate')
    def validate_date_format(cls, value):
        if value is None:
            return value
        allowed_formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]
        for fmt in allowed_formats:
            try:
                dt = datetime.strptime(value, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError("Incorrect date format. Allowed: YYYY-MM-DD, YYYY/MM/DD, DD-MM-YYYY, DD/MM/YYYY")


class taxonApi(BaseModel):
    id: int = Field(None, description="Taxon AphiaID.")
    commonname: Optional[str] = Field(None, description="common name of the species specified in the query")
    scientificname: Optional[str] = Field(None, description="scientific name of the species")
    annotationsrequested: Optional[bool] = Field(False, description="when the user request specifies scientific name annotations to be fetched from WoRMs")


class checklistApi(BaseModel):
    scientificname: Optional[str] = Field(None, 
                                          description="full scientific name", 
                                          examples=["Delphinus delphis", "Alosa pseudoharengus"])
    taxonid: Optional[str] = Field(None, description="Taxon AphiaID.")
    startdate: Optional[str] = Field(None, 
                                     description="Start date of query. Fetch records after this date. Should be of format YYYY-MM-DD")
    enddate: Optional[str] = Field(None, 
                                   description="End date of query. Fetch records before this date. Should be of format YYYY-MM-DD. Should be greater than startdate")
    areaid: Optional[str] = Field(None, description="")
    instituteid: Optional[str] = Field(None, description="")
    nodeid: Optional[str] = Field(None, description="")
    startdepth: Optional[int] = Field(None, 
                                      description="start depth of creature instance recorded in meters")
    enddepth: Optional[int] = Field(None, description="")
    geometry: Optional[str] = Field(None, description="Geometry, formatted as WKT or GeoHash. Polygon of a region provided in the query")
    absence: Optional[str] = Field(None, 
                                   description="Include absence records (include) or get absence records exclusively (true).")
    redlist: Optional[bool] = Field(None, description="Red List species only, true/false.")
    hab: Optional[bool] = Field(None, description="HAB species only, true/false.")
    wrims: Optional[bool] = Field(None, description="WRiMS species only, true/false.")
    flags: Optional[str] = Field(None, description="Comma separated list of quality flags which need to be set.")
    exclude: Optional[str] = Field(None, description="Comma separated list of quality flags to be excluded.")
    dropped: Optional[str] = Field(None, description="Include dropped records (include) or only dropped (true)")
    
    #extra parameters which are not mentioned in api documentation. 
    area: Optional[str] = Field(None, description="Name of the Area, place or region specified in the user request.")
    institute: Optional[str] = Field(None, description="Name of the institute in the request.")
    commonname: Optional[str] = Field(None, description="Common name passed in the user query")

    @field_validator('startdate', 'enddate')
    def validate_date_format(cls, value):
        allowed_formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]
        for format in allowed_formats:
            try:
                dt = datetime.strptime(value, format)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError("Incorrect date format. Allowed formats: YYYY-MM-DD, YYYY/MM/DD, DD-MM-YYYY, DD/MM/YYYY")
    
class statisticsApi(BaseModel):
    scientificname: Optional[Annotated[str, Field(description="Scientific name. Leave empty to include all taxa.")]] = None
    taxonid: Optional[Annotated[str, Field(description="Taxon AphiaID.")]] = None
    areaid: Optional[Annotated[str, Field(description="Area ID.")]] = None
    datasetid: Optional[Annotated[str, Field(description="Dataset UUID.")]] = None
    nodeid: Optional[Annotated[str, Field(description="Node UUID.")]] = None

    startdate: Optional[Annotated[str, Field(description="Start date formatted as YYYY-MM-DD.")]] = None
    enddate: Optional[Annotated[str, Field(description="End date formatted as YYYY-MM-DD.")]] = None

    startdepth: Optional[Annotated[int, Field(ge=0, description="Start depth, in meters (must be >= 0).")]] = None
    enddepth: Optional[Annotated[int, Field(ge=0, description="End depth, in meters (must be >= 0).")]] = None

    geometry: Optional[Annotated[str, Field(description="Geometry, formatted as WKT or GeoHash.")]] = None

    redlist: Optional[Annotated[bool, Field(description="Red List species only.")]] = None
    hab: Optional[Annotated[bool, Field(description="HAB species only.")]] = None
    wrims: Optional[Annotated[bool, Field(description="WRiMS species only.")]] = None

    dropped: Optional[Annotated[Literal["include", "true"], Field(description="Include dropped records or only dropped.")]] = None
    absence: Optional[Annotated[Literal["include", "true"], Field(description="Include absence records or only absence.")]] = None

    flags: Optional[Annotated[str, Field(description="Comma-separated list of quality flags to include.")]] = None
    exclude: Optional[Annotated[str, Field(description="Comma-separated list of quality flags to exclude.")]] = None

    # extra parameters which are not mentioned in api documentation. 
    area: Optional[str] = Field(None, description="Name of the Area, place or region specified in the user request.")
    institute: Optional[str] = Field(None, description="Name of the institute in the request.")
    commonname: Optional[str] = Field(None, description="common name of the species specified in the query")

    # extension for statistics api
    statistics_extensions: Optional[
            Annotated[
                List[Literal["years", "taxonomy", "composition"]],
                Field(
                    description=(
                        "Decide which OBIS statistics extensions are needed to answer the user's question. "
                        "Choose one or more of the following values ONLY:\n"
                        "- 'years': when the user asks about trends over time or year-wise counts\n"
                        "- 'taxonomy': when the user asks about species, genus, or taxonomic breakdowns\n"
                        "- 'composition': when the user asks about community structure or record composition\n"
                        "If none apply, return an empty list."
                    )
                )
            ]
        ]


    @field_validator('startdate', 'enddate')
    def validate_date_format(cls, value):
        allowed_formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]
        for format in allowed_formats:
            try:
                dt = datetime.strptime(value, format)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError("Incorrect date format. Allowed formats: YYYY-MM-DD, YYYY/MM/DD, DD-MM-YYYY, DD/MM/YYYY")
    