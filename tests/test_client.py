import pytest

def test_client_profile_unauthenticated(client):
    response = client.get("/client/profile")
    assert response.status_code == 401