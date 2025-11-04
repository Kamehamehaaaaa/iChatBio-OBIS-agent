from pydantic import BaseModel, field_validator, Field, constr, conint
from typing import Optional, Annotated, Literal, Required
from datetime import datetime

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

class facetsAPIParams(BaseModel):
    facets: list = Field(None, description="Comma separated list of facets", examples= ["originalScientificName,flags", "node_id"])
    composite: Optional[bool] = Field(None, description="Composite aggregation")
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