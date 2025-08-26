import importlib.resources
from abc import ABC, abstractmethod
from typing import Iterator

from query_collection import TemplateQueryCollection
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DC


class MetadataStore(ABC):
    @abstractmethod
    def identifiers(self, **kwargs) -> Iterator[dict]:
        """This method return identifier dicts.

        kwargs: are the named arguments that can be used to restrict the records to be returned.
            If the field identifier is specifeid, the exact record is yielded or nothing.
            If the fields from or until are specifeid the records are restricted according to their date property.
            If the field set is specifeid … not yet implemented.

        returns an iterator of identifier dicts.
        These are the same as returned by records, just the metadata might not be included.
        """

    @abstractmethod
    def records(self, **kwargs) -> Iterator[dict]:
        """This method return record dicts.

        kwargs: are the named arguments that can be used to restrict the records to be returned.
            If the field identifier is specifeid, the exact record is yielded or nothing.
            If the fields from or until are specifeid the records are restricted according to their date property.
            If the field set is specifeid … not yet implemented.

        returns an iterator of record dicts.
        These are the same as returned by identifiers, but the metadata is required.
        """


class MockMetadataStore(MetadataStore):
    """Sample metadata store (you would replace this with your actual database or storage)"""

    metadata_store = [
        {"identifier": "record1", "datestamp": "2025-08-14", "title": "Record 1"},
        {"identifier": "record2", "datestamp": "2025-08-10", "title": "Record 2"},
    ]

    def records(self, **kwargs):
        for rec in self._records(**kwargs):
            yield {**rec, "metadata": self.get_graph(**rec)}

    identifiers = records

    def _records(self, **kwargs):
        identifier = kwargs.get("identifier")
        from_value = kwargs.get("from")
        until = kwargs.get("until")
        set_value = kwargs.get("set")
        for rec in self.metadata_store:
            if from_value and rec["datestamp"] < from_value:
                continue
            if until and rec["datestamp"] > until:
                continue
            if identifier:
                if rec["identifier"] == identifier:
                    yield rec
                    return
            else:
                yield rec

    def get_graph(self, identifier, title, **kwargs):
        g = Graph()
        g.add((URIRef(f"urn:id:{identifier}"), DC.title, Literal(title)))
        return g


class SparqlMetadataStore(MetadataStore):
    def __init__(self, graph: Graph, queries: TemplateQueryCollection):
        self.graph = graph
        self.queries = queries

    def identifiers(self, **kwargs):
        identifier = kwargs.get("identifier")
        from_value = kwargs.get("from")
        until = kwargs.get("until")
        set_value = kwargs.get("set")

        headersSelect = None
        if identifier:
            headersSelect = self.queries.get("identifiedHeaderSelect").p(
                identifier=Literal(identifier)
            )
        elif from_value or until:
            dateRange = {}
            if from_value:
                dateRange["from"] = Literal(from_value)
            if until:
                dateRange["until"] = Literal(until)
            headersSelect = self.queries.get("dateRangeHeadersSelect").p(**dateRange)
        else:
            headersSelect = self.queries.get("allHeadersSelect").p()

        try:
            for row in self.graph.query(**headersSelect):
                yield row.asdict()
        except Exception as e:
            raise StoreBackendException("Backend not available or invalid query.", e)

    def records(self, **kwargs):
        for header in self.identifiers(**kwargs):
            yield {**header, "metadata": self.metadata(header["identifier"])}

    def metadata(self, identifier):
        try:
            recordConstruct = self.queries.get("recordConstruct")
            metadata = self.graph.query(
                **(recordConstruct.p(identifier=Literal(identifier)))
            ).graph
            # hack, construct result only contain the default namespace_manager
            # overwrite it to have all namespaces as defined on the store
            metadata.namespace_manager = self.graph.namespace_manager
            return metadata
        except Exception as e:
            raise StoreBackendException("Backend not available or invalid query.", e)


class MockSparqlMetadataStore(SparqlMetadataStore):
    def __init__(self):
        with (
            importlib.resources.path(
                self.__module__, "../example/data.ttl"
            ) as graph_path,
            importlib.resources.path(
                self.__module__, "../example/queries"
            ) as query_path,
        ):
            self.graph = Graph().parse(source=graph_path, format="turtle")
            self.queries = TemplateQueryCollection(initNs=dict(self.graph.namespaces()))
            self.queries.loadFromDirectory(query_path)


class StoreException(Exception):
    """Exceptions that are raised in the Store."""


class StoreBackendException(StoreException):
    """Exceptions that are raised in the Store."""
