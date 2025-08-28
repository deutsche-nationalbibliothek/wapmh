import dataclasses
from abc import abstractmethod
from typing import Any

from fastapi import Request
from rdflib import Graph
from xsdata.formats.dataclass.etree import etree

from .model.oai_pmh import (
    HeaderType,
    MetadataType,
    RecordType,
    RequestType,
)
from .store import MetadataStore


class RequestAdapter:
    fields = {
        f.metadata.get("name") or f.name: f for f in dataclasses.fields(RequestType)
    }
    """`fields` is a mapping of a request parameter to the respective dataclass field."""

    @classmethod
    def request(cls, request: Request) -> RequestType:
        """Convert a starlet/fastapi request to a OAI-PMH RequestType.

        Especially this conversion is required to translate some field names that are reserved words in python.
        Those words hold the parameter name in the metadate field 'name'.
        e.g. the `from` paramter is handles as `from_value` and `metadataPrefix` as `metadata_prefix`.
        """
        request_fields = {
            cls.fields[key].name: request.query_params[key]
            for key in request.query_params
            if key in cls.fields
        }
        return RequestType(
            **dict(request_fields),
            value=str(request.base_url),
        )


class MetadataAdapter:
    def __init__(self, store):
        self.store = store

    def record(self, **kwargs) -> RecordType:
        """Get a single record according to the metadataPrefix."""
        for record in self.records(**kwargs):
            return record

    def records(self, **kwargs) -> list[RecordType]:
        """Get records according to the metadataPrefix."""
        for rec in self.store.records(**kwargs):
            yield RecordType(
                header=HeaderType(
                    identifier=rec.get("identifier"),
                    datestamp=rec.get("datestamp"),
                    set_spec=[],
                ),
                metadata=self.metadata(rec.get("metadata")),
            )

    @abstractmethod
    def metadata(self, metadata: Any) -> MetadataType:
        """Get a record according to the metadataPrefix."""
        pass


class RdfMetadataAdapter(MetadataAdapter):
    def metadata(self, metadata: Graph) -> MetadataType:
        """Convert the metadata according to the metadataPrefix."""
        rdf_string = metadata.serialize(format="application/rdf+xml", encoding="utf-8")
        rdf_elements = etree.fromstring(rdf_string)
        return MetadataType(other_element=rdf_elements)


class MetadataAdapterRegistry:
    def __init__(self):
        self.registry = {}

    def register(self, metadataPrefix, adapterClass):
        self.registry[metadataPrefix] = adapterClass

    def adapter(self, store: MetadataStore, metadataPrefix) -> MetadataAdapter:
        return self.registry[metadataPrefix](store)
