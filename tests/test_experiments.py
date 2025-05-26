from wapmh.repository import app
from fastapi.testclient import TestClient
from loguru import logger
from dataclasses import dataclass, field
from xsdata.formats.converter import Converter, converter
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.parsers import XmlParser
from typing import Optional

client = TestClient(app)


def test_custom_type():
    serializer = XmlSerializer()

    class MyRDF(str):
        pass

    @dataclass
    class Example:
        contents: MyRDF = field()

    class MyRDFConverter(Converter):
        def deserialize(self, value: str, **kwargs) -> MyRDF:
            return MyRDF(value)

        def serialize(self, value: MyRDF, **kwargs) -> str:
            return value

    converter.register_converter(MyRDF, MyRDFConverter())
    output = serializer.render(Example(MyRDF("<hallo>hi</hallo>")))
    logger.info(f"response:\n{output}")


def test_parse():
    @dataclass
    class WrapperType:
        """The Type to hold any RDF data"""

        class Meta:
            name = "wrapper"

        other_element: Optional[object] = field(
            metadata={
                "type": "Wildcard",
                "namespace": "##any",
            },
        )

    @dataclass
    class RecordType:
        class Meta:
            name = "Record"

        header: str = field(default="Some info", metadata={"type": "Attribute"})
        wrapper: Optional[WrapperType] = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )

    rdf_string = """<?xml version="1.0" encoding="utf-8"?>
    <rdf:RDF
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    >
    <rdf:Description rdf:about="urn:id:record2">
    <dc:title>Record 2</dc:title>
    </rdf:Description>
    <rdf:Description rdf:about="urn:id:record3">
      <dc:title>Record 3</dc:title>
    </rdf:Description>
    </rdf:RDF>
    """
    rdf_data = rdf_string.splitlines()
    metadata_string = f"""{rdf_data[0]}
        <wrapper>
        {"\n".join(rdf_data[1:])}
        </wrapper>
        """
    model = RecordType(
        header="Here comes the data",
        wrapper=XmlParser().from_string(metadata_string, WrapperType),
    )

    output = XmlSerializer().render(
        model,
        ns_map={
            "dc": "http://purl.org/dc/elements/1.1/",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        },
    )
    logger.info(f"response:\n{output}")
