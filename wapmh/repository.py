import dataclasses
from contextlib import asynccontextmanager
from functools import lru_cache

import fastapi_xml.response
from fastapi import FastAPI, Request
from fastapi_xml import XmlAppResponse
from query_collection import TemplateQueryCollection
from rdflib import Graph
from stringcase import snakecase
from xsdata.formats.dataclass.etree import etree
from xsdata.models.datatype import XmlDateTime

from . import config
from .model.oai_pmh import (
    DescriptionType,
    GetRecordType,
    HeaderType,
    IdentifyType,
    ListIdentifiersType,
    ListMetadataFormatsType,
    ListRecordsType,
    ListSetsType,
    MetadataFormatType,
    MetadataType,
    OaiPmh,
    OaiPmherrorcodeType,
    OaiPmherrorType,
    RecordType,
    RequestType,
    ResumptionTokenType,
    SetType,
)
from .store import MetadataStore, SparqlMetadataStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run at startup
    Initialize the Client and add it to request.state
    """
    settings = get_settings()

    graph = Graph().parse(source=settings.graph_path, format="turtle")
    queries = TemplateQueryCollection(initNs=dict(graph.namespaces()))
    queries.loadFromDirectory(settings.query_path)
    metadata_store = SparqlMetadataStore(graph=graph, queries=queries)
    yield {"metadata_store": metadata_store}
    """ Run on shutdown
        Close the connection
        Clear variables and release the resources
    """
    pass


app = FastAPI(lifespan=lifespan)

# Make sure the OAI namespace is set as default namespace
fastapi_xml.response.NS_MAP = {None: "http://www.openarchives.org/OAI/2.0/"}


@lru_cache
def get_settings():
    return config.Settings()


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
                **globals()[snakecase(verb)](
                    request.state.metadata_store, **query_params
                ),
            )
        )
    else:
        return XmlAppResponse(
            OaiPmh(
                error=OaiPmherrorType(
                    value="Invalid verb", code=OaiPmherrorcodeType.BAD_VERB
                )
            )
        )


def get_record(
    metadata_store: MetadataStore, metadataPrefix: str, identifier: str, **kwargs
) -> dict:
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


def identify(metadata_store: MetadataStore, **kwargs) -> dict:
    """Implements the Identify verb."""
    settings = get_settings()
    return {
        "identify": IdentifyType(
            repository_name=settings.repository_name,
            base_url="",
            protocol_version="2.0",
            admin_email=settings.admin_emails,
            earliest_datestamp="",
            deleted_record="",
            granularity="",
            compression=[""],
            description=[DescriptionType(settings.description)],
        )
    }


def list_identifiers(
    metadata_store: MetadataStore,
    metadataPrefix: str,
    **kwargs,
) -> dict:
    """Implements the ListIdentifiers verb."""
    return {
        "list_identifiers": ListIdentifiersType(
            header=[
                HeaderType(
                    identifier=rec.get("identifier"),
                    datestamp=rec.get("datestamp"),
                    set_spec=[],
                )
                for rec in metadata_store.records(**kwargs)
            ],
            resumption_token=None,
        )
    }
    # TODO: return an error in case of an empty result


def list_metadata_formats(
    metadata_store: MetadataStore, identifier: str = None, **kwargs
) -> dict:
    """Implements the ListMetadataFormats verb."""
    return {
        "list_metadata_formats": ListMetadataFormatsType(
            metadata_format=[MetadataFormatType()]
        )
    }


def list_records(metadata_store: MetadataStore, metadataPrefix: str, **kwargs) -> dict:
    """Implements the ListRecords verb."""
    return {
        "list_records": ListRecordsType(
            record=[
                get_record_type(rec, metadataPrefix)
                for rec in metadata_store.records(**kwargs)
            ]
        )
    }
    # TODO: return an error in case of an empty result


def list_sets(metadata_store: MetadataStore, **kwargs) -> dict:
    """Implements the ListSets verb."""

    return {
        "error": OaiPmherrorType(
            value="Record not found", code=OaiPmherrorcodeType.NO_SET_HIERARCHY
        )
    }

    return {
        "list_sets": ListSetsType(
            set=[SetType()], resumption_token=ResumptionTokenType()
        )
    }


def get_record_type(rec, metadataPrefix) -> RecordType:
    """Get a record according to the metadataPrefix."""
    g = rec.get("metadata")
    rdf_string = g.serialize(format="application/rdf+xml", encoding="utf-8")
    rdf_elements = etree.fromstring(rdf_string)
    return RecordType(
        header=HeaderType(
            identifier=rec.get("identifier"),
            datestamp=rec.get("datestamp"),
            set_spec=[],
        ),
        metadata=MetadataType(other_element=rdf_elements),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
