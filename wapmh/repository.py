from fastapi import FastAPI, Request
from fastapi_xml import XmlAppResponse
import fastapi_xml.response
from stringcase import snakecase
from .model.oai_pmh import *
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import DC
import dataclasses
from xsdata.formats.dataclass.etree import etree
from loguru import logger

app = FastAPI()

fastapi_xml.response.NS_MAP = {None: "http://www.openarchives.org/OAI/2.0/"}


class MetadataStore:
    # Sample metadata store (you would replace this with your actual database or storage)
    metadata_store = [
        {"id": "record1", "title": "Record 1", "date": "2025-08-14"},
        {"id": "record2", "title": "Record 2", "date": "2025-08-10"},
    ]

    def records(self, **kwargs):
        identifier = kwargs.get("identifier")
        from_ = kwargs.get("from")
        until = kwargs.get("until")
        set_ = kwargs.get("set")
        for rec in self.metadata_store:
            if from_ and rec["date"] < from_:
                continue
            if until and rec["date"] > until:
                continue
            if identifier:
                if rec["id"] == identifier:
                    yield rec
                    return
            else:
                yield rec


metadata_store = MetadataStore()


@app.get("/", response_class=XmlAppResponse)
async def oai_pmh(verb: str, request: Request = None) -> XmlAppResponse:
    """The OAI-PMH interface method.

    See also: https://www.openarchives.org/OAI/openarchivesprotocol.html
    """
    if verb in [
        "GetRecord",
        "Identify",
        "ListIdentifiers",
        "ListMetadataFormats",
        "ListRecords",
        "ListSets",
    ]:
        query_params = dict(request.query_params)
        if "metadataPrefix" not in query_params:
            query_params["metadataPrefix"] = "oai_dc"
        return XmlAppResponse(
            OaiPmh(
                response_date=XmlDateTime.now(),
                request=RequestType(
                    **{
                        key: request.query_params[key]
                        for key in request.query_params
                        if key in [f.name for f in dataclasses.fields(RequestType)]
                    },
                    value=str(request.base_url),
                ),
                **globals()[snakecase(verb)](**query_params),
            )
        )
    else:
        # todo return proper http code and an xml body
        return {"error": "Invalid verb"}


def get_record(metadataPrefix: str, identifier: str, **kwargs) -> dict:
    """Implements the GetRecord verb."""
    for rec in metadata_store.records(identifier=identifier):
        return {
            "get_record": GetRecordType(record=get_record_type(rec, metadataPrefix))
        }

    return {
        "error": OaiPmherrorType(
            value="Record not found", code=OaiPmherrorcodeType.ID_DOES_NOT_EXIST
        )
    }


def identify(**kwargs) -> dict:
    """Implements the Identify verb."""
    return {
        "identify": IdentifyType(
            repository_name="",
            base_url="",
            protocol_version="2.0",
            admin_email=[""],
            earliest_datestamp="",
            deleted_record="",
            granularity="",
            compression=[""],
            description=[DescriptionType("My Description")],
        )
    }


def list_identifiers(
    metadataPrefix: str,
    **kwargs,
) -> dict:
    """Implements the ListIdentifiers verb."""
    return {
        "list_identifiers": ListIdentifiersType(
            header=[
                HeaderType(identifier=rec["id"], datestamp=rec["date"], set_spec=[])
                for rec in metadata_store.records(**kwargs)
            ],
            resumption_token=ResumptionTokenType(),
        )
    }


def list_metadata_formats(identifier: str = None, **kwargs) -> dict:
    """Implements the ListMetadataFormats verb."""
    return {
        "list_metadata_formats": ListMetadataFormatsType(
            metadata_format=[MetadataFormatType()]
        )
    }


def list_records(metadataPrefix: str, **kwargs) -> dict:
    """Implements the ListRecords verb."""
    return {
        "list_records": ListRecordsType(
            record=[
                get_record_type(rec, metadataPrefix)
                for rec in metadata_store.records(**kwargs)
            ]
        )
    }


def list_sets(**kwargs) -> dict:
    """Implements the ListSets verb."""
    return {
        "list_sets": ListSetsType(
            set=[SetType()], resumption_token=ResumptionTokenType()
        )
    }


def get_record_type(rec, metadataPrefix) -> RecordType:
    """Get a record according to the metadataPrefix."""
    g = Graph()
    g.add((URIRef(f"urn:id:{rec['id']}"), DC.title, Literal(rec["title"])))
    rdf_string = g.serialize(format="application/rdf+xml", encoding="utf-8")
    rdf_elements = etree.fromstring(rdf_string)
    logger.debug(rdf_elements)
    return RecordType(
        header=HeaderType(identifier=rec["id"], datestamp=rec["date"], set_spec=[]),
        metadata=MetadataType(other_element=rdf_elements),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
