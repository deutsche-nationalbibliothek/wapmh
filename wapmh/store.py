import importlib.resources
from abc import ABC, abstractmethod
from typing import Iterator

from query_collection import TemplateQueryCollection
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DC


class MetadataStore(ABC):
    @abstractmethod
    def records(self, **kwargs) -> Iterator[dict]:
        """This method return record dicts.

        kwargs: are the named arguments that can be used to restrict the records to be returned.
            If the field identifier is specifeid, the exact record is yielded or nothing.
            If the fields from or until are specifeid the records are restricted according to their date property.
            If the field set is specifeid … not yet implemented.

        returns an iterator of record dicts.
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

    def _records(self, **kwargs):
        identifier = kwargs.get("identifier")
        from_ = kwargs.get("from")
        until = kwargs.get("until")
        set_ = kwargs.get("set")
        for rec in self.metadata_store:
            if from_ and rec["datestamp"] < from_:
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

    def records(self, **kwargs):
        identifier = kwargs.get("identifier")
        from_ = kwargs.get("from")
        until = kwargs.get("until")
        set_ = kwargs.get("set")

        headersSelect = None
        if identifier:
            headersSelect = self.queries.get("identifiedHeaderSelect").p(
                identifier=Literal(identifier)
            )
        elif from_ or until:
            dateRange = {}
            if from_:
                dateRange["from"] = Literal(from_)
            if until:
                dateRange["until"] = Literal(until)
            headersSelect = self.queries.get("dateRangeHeadersSelect").p(**dateRange)
        else:
            headersSelect = self.queries.get("allHeadersSelect").p()

        recordConstruct = self.queries.get("recordConstruct")
        for row in self.graph.query(**headersSelect):
            metadata = self.graph.query(
                **(recordConstruct.p(identifier=Literal(row["identifier"])))
            ).graph
            # hack, construct result only contain the default namespace_manager
            # overwrite it to have all namespaces as defined on the store
            metadata.namespace_manager = self.graph.namespace_manager
            yield {**(row.asdict()), "metadata": metadata}


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
