import dataclasses
from contextlib import asynccontextmanager
from functools import lru_cache

import fastapi_xml.response
from fastapi import FastAPI, Request
from fastapi_xml import XmlAppResponse
from query_collection import TemplateQueryCollection
from rdflib import Graph
from rdflib.plugins.stores.sparqlstore import SPARQLStore
from stringcase import snakecase
from xsdata.models.datatype import XmlDateTime

from . import config
from .adapters import MetadataAdapterRegistry, RdfMetadataAdapter, RequestAdapter
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
    OaiPmh,
    OaiPmherrorcodeType,
    OaiPmherrorType,
    ResumptionTokenType,
    SetType,
)
from .store import MetadataStore, SparqlMetadataStore, StoreException


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run at startup
    Initialize the Client and add it to request.state
    """
    yield {"metadata_store": get_metadata_store()}
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


@lru_cache
def get_metadata_store():
    settings = get_settings()
    if settings.graph_path:
        graph = Graph().parse(source=settings.graph_path, format="turtle")
    elif settings.sparql_endpoint:
        store = SPARQLStore(query_endpoint=settings.sparql_endpoint)
        graph = Graph(store=store)
    else:
        raise Exception(
            "No graph configured. You need to set a SPARQL_ENDPOINT or GRAPH_PATH."
        )
    if settings.query_path:
        queries = TemplateQueryCollection()
        queries.loadFromDirectory(settings.query_path)
    else:
        raise Exception("No queries configured. You need to set a QUERY_PATH.")
    return SparqlMetadataStore(graph=graph, queries=queries)


@lru_cache
def get_record_adapter_registry() -> MetadataAdapterRegistry:
    registry = MetadataAdapterRegistry()
    registry.register("oai_dc", RdfMetadataAdapter)
    registry.register("rdf", RdfMetadataAdapter)
    return registry


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

        try:
            return XmlAppResponse(
                OaiPmh(
                    response_date=XmlDateTime.now(),
                    request=RequestAdapter.request(request),
                    **globals()[snakecase(verb)](
                        request.state.metadata_store, **query_params
                    ),
                )
            )
        except StoreException:
            return XmlAppResponse(
                status_code=500,
                content=ApplicationErrorType(
                    value="500 Internal Server Error: Store Exception"
                ),
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
    adapter = get_record_adapter_registry().adapter(metadata_store, metadataPrefix)
    if record := adapter.record(identifier=identifier):
        return {"get_record": GetRecordType(record=record)}

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
                for rec in metadata_store.identifiers(**kwargs)
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
    adapter = get_record_adapter_registry().adapter(metadata_store, metadataPrefix)
    return {"list_records": ListRecordsType(record=list(adapter.records(**kwargs)))}
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


@dataclasses.dataclass
class ApplicationErrorType:
    class Meta:
        name = "ApplicationError"

    value: str = dataclasses.field(
        default="",
        metadata={
            "required": True,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
