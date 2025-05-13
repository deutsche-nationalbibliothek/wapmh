from fastapi import FastAPI, Response, Request
from dataclasses import dataclass, field
from fastapi_xml import XmlAppResponse
import xml.etree.ElementTree as ET
from loguru import logger
from stringcase import snakecase

app = FastAPI()

# Sample metadata store (you would replace this with your actual database or storage)
metadata_store = {
    "records": [
        {"id": "record1", "title": "Record 1"},
        {"id": "record2", "title": "Record 2"}
    ]
}

@dataclass
class Record:
    record: dict[str, str]

@dataclass
class MetadataSet:
    records: list[Record]

@dataclass
class OAI_PMH:
    metadataSet: MetadataSet

@dataclass
class EX:
    bla: str

@app.get("/", response_class=XmlAppResponse)
async def oai_pmh(verb: str, request: Request = None) -> XmlAppResponse:
    if verb in ["Identify", "ListMetadataFormats", "GetRecord", "ListSets", "ListIdentifiers", "ListRecords"]:
        logger.debug(globals())
        return XmlAppResponse(globals()[snakecase(verb)](**request.query_params))
    else:
        # todo return proper http code and an xml body
        return {"error": "Invalid verb"}

def list_records(metadataPrefix: str, **kwargs) -> dict:
    root = ET.Element("OAI-PMH")
    metadataSet = ET.SubElement(root, "metadataSet")
    records = ET.SubElement(metadataSet, "records")
    record = ET.SubElement(records, "record")
    header = ET.SubElement(record, "header")
    metadata = ET.SubElement(record, "metadata")
    about = ET.SubElement(record, "about")

    logger.debug(root)
    logger.debug(metadata)
    logger.debug(records)

    for record in metadata_store["records"]:
        logger.debug(record)
        rec = ET.SubElement(records, "record", {"identifier": record["id"]})
        title = ET.SubElement(rec, "title").text = record["title"]

    # return EX(bla="hallo")
    return OAI_PMH(metadataSet="hallo")

def get_record(metadataPrefix: str, identifier: str, **kwargs) -> dict:
    for rec in metadata_store["records"]:
        if rec["id"] == identifier:
            title = ET.SubElement(ET.Element("record"), "title").text = rec["title"]
            return {
                "__root__": ET.Element("OAI-PMH"),
                "metadataSet": ET.SubElement(__root__, "metadataSet"),
                "record": ET.SubElement(metadata, "record", {"identifier": identifier})
            }

    return {"error": "Record not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
