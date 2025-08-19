from abc import ABC, abstractmethod
from textwrap import dedent
from typing import Any, Iterator, Mapping, Optional, Union

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DC
from rdflib.plugins.sparql.sparql import Query


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
    def __init__(self, graph: Graph, queries: dict):
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
            headersSelect = self.queries.get("dateRangeHeadersSelect").p(
                **{"from": Literal(from_), "until": Literal(until)}
            )
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


class TemplateQueryCollection(dict):
    def __init__(self, queries: dict = {}, initNs: Optional[Mapping[str, Any]] = None):
        self.queries = queries
        self.initNs = initNs

    def get(self, key):
        query_object = self.queries.get(key)
        if not isinstance(query_object, TemplateQuery):
            return TemplateQuery(query_object=query_object, initNs=self.initNs)
        else:
            return query_object

    def set(self, key, val):
        self.queries[key] = val


class TemplateQuery:
    def __init__(
        self,
        query_object: Union[str, Query],
        initNs: Optional[Mapping[str, Any]] = None,
    ):
        self.query_object = query_object
        self.initNs = initNs

    def prepare(self, **initBindings):
        return {
            "query_object": self.query_object,
            "initNs": self.initNs,
            "initBindings": initBindings,
        }

    p = prepare


metadata = """
@prefix bibo: <http://purl.org/ontology/bibo/> .
@prefix lv:   <http://purl.org/lobid/lv#> .
@prefix bf: <http://id.loc.gov/ontologies/bibframe/> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdau: <http://rdaregistry.info/Elements/u/> .
@prefix wdrs: <http://www.w3.org/2007/05/powder-s#> .
@prefix gndo: <https://d-nb.info/standards/elementset/gnd#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

<https://d-nb.info/1334427879> a bibo:Periodical, lv:ArchivedWebPage, <http://data.archiveshub.ac.uk/def/ArchivalResource>, bf:Archival;
  dc:identifier "(DE-101)1334427879";
  dc:date "" ;
  foaf:primaryTopic <https://www.dmg-ev.de/> ;
  lv:webPageArchived <https://www.dmg-ev.de/> ;
  rdau:P60049 <https://d-nb.info/gnd/4596172-4>;
  dc:title "Deutsche Meteorologische Gesellschaft e.V., DMG";
  wdrs:describedby <https://d-nb.info/1334427879/about> .

<https://d-nb.info/1352272679> dcterms:medium <http://rdaregistry.info/termList/RDACarrierType/1018>;
  rdau:P60049 <http://rdaregistry.info/termList/RDAContentType/1020>;
  rdau:P60050 <http://rdaregistry.info/termList/RDAMediaType/1003>;
  rdau:P60048 <http://rdaregistry.info/termList/RDACarrierType/1018>;
  dc:identifier "(DE-101)1352272679";
  rdau:P60049 <https://d-nb.info/gnd/4596172-4>;
  dcterms:isPartOf <https://d-nb.info/1334427879>;
  wdrs:describedby <https://d-nb.info/1352272679/about> .

<https://d-nb.info/1352272679/about> dcterms:license <http://creativecommons.org/publicdomain/zero/1.0/>;
  dcterms:modified "2024-12-30T18:01:13.000"^^xsd:dateTime .

<https://d-nb.info/1352272679> dcterms:issued "2024";
  bibo:issue "2024-12-21";
  owl:sameAs <http://hub.culturegraph.org/resource/DNB-1352272679> .
"""

graph = Graph().parse(data=metadata, format="turtle")

tqc = TemplateQueryCollection(initNs=dict(graph.namespaces()))
tqc.set(
    "identifiedHeaderSelect",
    dedent("""
            prefix bibo: <http://purl.org/ontology/bibo/>
            prefix lv:   <http://purl.org/lobid/lv#>
            prefix bf: <http://id.loc.gov/ontologies/bibframe/>
            select ?identifier ?datestamp {
                ?resourceIri a lv:ArchivedWebPage ;
                dc:identifier ?identifier .
            }
            """),
)
tqc.set("dateRangeHeadersSelect", tqc.get("identifiedHeaderSelect"))
tqc.set("allHeadersSelect", tqc.get("identifiedHeaderSelect"))
tqc.set(
    "recordConstruct",
    dedent("""
            prefix bibo: <http://purl.org/ontology/bibo/>
            prefix lv:   <http://purl.org/lobid/lv#>
            prefix bf: <http://id.loc.gov/ontologies/bibframe/>
            prefix dc: <http://purl.org/dc/elements/1.1/>

            construct where {
                ?resourceIri a lv:ArchivedWebPage ;
                    dc:identifier ?identifier ;
                    ?p ?o .
            }
            """),
)

mocked_sparql_metadata_store = SparqlMetadataStore(graph, tqc)
