from wapmh.repository import app
from fastapi.testclient import TestClient
from loguru import logger

client = TestClient(app)


def test_list_records():
    response = client.get("/", params={"verb": "ListRecords"})
    assert response.status_code == 200
    if "<rdf:RDF" not in response.text:
        logger.info(f"response:\n{response.text}")
    assert "<rdf:RDF" in response.text
