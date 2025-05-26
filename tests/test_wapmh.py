from wapmh.repository import app
from fastapi.testclient import TestClient


client = TestClient(app)


def test_list_records():
    response = client.get("/", params={"verb": "ListRecords"})
    assert response.status_code == 200
