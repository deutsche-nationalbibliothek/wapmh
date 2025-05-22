from oaipmh.server import ServerBase
from oaipmh.metadata import MetadataRegistry


def test_simple_request():
    registry = MetadataRegistry()
    # xmlserver = XMLTreeServer()
    server = ServerBase(xmlserver, registry)

    request = {"verb": "listSets"}
    server.handleRequest(request)
