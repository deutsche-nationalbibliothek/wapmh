from fastapi import FastAPI, Response, Request
from dataclasses import dataclass, field
from fastapi_xml import XmlAppResponse
import fastapi_xml.response
from loguru import logger
from stringcase import snakecase
from .model.oai_pmh import *

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
        return XmlAppResponse(globals()[snakecase(verb)](**query_params))
    else:
        # todo return proper http code and an xml body
        return {"error": "Invalid verb"}


def list_records(metadataPrefix: str, **kwargs) -> dict:
    # logger.debug(metadata)
    # logger.debug(records)

    for record in metadata_store["records"]:
        logger.debug(record)
        rec = RecordType(header=HeaderType(identifier=record["id"]))
        # title = ET.SubElement(rec, "title").text = record["title"]

    # return EX(bla="hallo")
    return OaiPmh()


def get_record(metadataPrefix: str, identifier: str, **kwargs) -> dict:
    for rec in metadata_store["records"]:
        if rec["id"] == identifier:
            title = ET.SubElement(ET.Element("record"), "title").text = rec["title"]
            return {
                "__root__": ET.Element("OAI-PMH"),
                "metadataSet": ET.SubElement(__root__, "metadataSet"),
                "record": ET.SubElement(metadata, "record", {"identifier": identifier}),
            }
            return OaiPmh()

    return OaiPmh(
        error=OaiPmherrorType(
            value="Record not found", code=OaiPmherrorcodeType.ID_DOES_NOT_EXIST
        )
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
