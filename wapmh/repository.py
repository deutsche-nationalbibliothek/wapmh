from fastapi import FastAPI, Request
from fastapi_xml import XmlAppResponse
import fastapi_xml.response
from loguru import logger
from stringcase import snakecase
from .model.oai_pmh import *
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import DC
import dataclasses

app = FastAPI()

fastapi_xml.response.NS_MAP = {None: "http://www.openarchives.org/OAI/2.0/"}

# Sample metadata store (you would replace this with your actual database or storage)
metadata_store = {
    "records": [
        {"id": "record1", "title": "Record 1"},
        {"id": "record2", "title": "Record 2"},
    ]
}


@app.get("/", response_class=XmlAppResponse)
async def oai_pmh(verb: str, request: Request = None) -> XmlAppResponse:
    if verb in [
        "Identify",
        "ListMetadataFormats",
        "GetRecord",
        "ListSets",
        "ListIdentifiers",
        "ListRecords",
    ]:
        logger.debug(globals())
        query_params = dict(request.query_params)
        if "metadataPrefix" not in query_params:
            query_params["metadataPrefix"] = "oai_dc"
        return XmlAppResponse(
            globals()[snakecase(verb)](**query_params, request=request)
        )
    else:
        # todo return proper http code and an xml body
        return {"error": "Invalid verb"}


def list_records(metadataPrefix: str, **kwargs):
    return OaiPmh(
        **oaiPmhBoilerplate(kwargs["request"]),
        list_records=ListRecordsType(
            record=[
                get_record_type(rec, metadataPrefix)
                for rec in metadata_store["records"]
            ]
        ),
    )


def get_record_type(rec, metadataPrefix):
    g = Graph()
    g.add((URIRef(f"urn:id:{rec['id']}"), DC.title, Literal(rec["title"])))
    return RecordType(
        header=HeaderType(identifier=rec["id"]),
        metadata=MetadataType(g.serialize(format="application/rdf+xml")),
    )


def get_record(metadataPrefix: str, identifier: str, **kwargs) -> dict:
    for rec in metadata_store["records"]:
        if rec["id"] == identifier:
            return OaiPmh(
                **oaiPmhBoilerplate(kwargs["request"]),
                get_record=GetRecordType(record=get_record_type(rec, metadataPrefix)),
            )

    return OaiPmh(
        **oaiPmhBoilerplate(kwargs["request"]),
        error=OaiPmherrorType(
            value="Record not found", code=OaiPmherrorcodeType.ID_DOES_NOT_EXIST
        ),
    )


def oaiPmhBoilerplate(request):
    return {
        "response_date": XmlDateTime.now(),
        "request": RequestType(
            **{
                key: request.query_params[key]
                for key in request.query_params
                if key in [f.name for f in dataclasses.fields(RequestType)]
            },
            value=str(request.base_url),
        ),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
