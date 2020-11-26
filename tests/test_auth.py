"""Test authorisation."""
import pytest
from starlette.testclient import TestClient

from storage import auth
from storage.app import app


def test_request_without_a_token():
    """
    Test a request made without a token.

    Making a request without an Authorization header should give a 401 error.
    """
    client = TestClient(app)
    response = client.post("/proposal/submit")
    assert response.status_code == 401


def test_request_without_bearer_keyword(monkeypatch):
    """
    Test a request without the Bearer keyword and a valid token.

    Making a request without the Bearer keyword in the Authorization header should
    give a 401 error, even if the token in the header value is valid.
    """

    def mock_parse_token(*args, **kwargs):
        return {"roles": ["Admin"]}

    monkeypatch.setattr(auth, "parse_token", mock_parse_token)
    client = TestClient(app)
    response = client.post("/proposal/submit", headers={"Authorization": "abcd"})
    assert response.status_code == 401


def test_request_with_invalid_token(monkeypatch):
    """
    Test a request with an invalid token.

    Making a request with an invalid token in the Authorization header should give a 401
    error.
    """

    def mock_parse_token(*args, **kwargs):
        raise Exception("Invalid token.")

    monkeypatch.setattr(auth, "parse_token", mock_parse_token)
    client = TestClient(app)
    response = client.post("/proposal/submit", headers={"Authorization": "Bearer abcd"})
    assert response.status_code == 401


@pytest.mark.parametrize("roles", [[], ["Guest"], ["No Admin"]])
def test_request_with_valid_token_without_admin_scope(monkeypatch, roles):
    """
    Test a request with a valid token without Admin scope.

    Making a request with a valid token which doesn't have Admin scope should give a 403
    error.
    """

    def mock_parse_token(*args, **kwargs):
        return {"roles": roles}

    monkeypatch.setattr(auth, "parse_token", mock_parse_token)
    client = TestClient(app)
    response = client.post("/proposal/submit", headers={"Authorization": "Bearer abcd"})
    assert response.status_code == 403


def test_requests_with_valid_token_with_admin_scope(monkeypatch):
    """
    Test a request with a valid token with Admin scope.

    Making a request with a valid token which has Admin scope should authorise the
    user.

    If the user is authorised, FastAPI tries to parse the request payload. As this
    fails, we expect a 422 error in this case.
    """

    def mock_parse_token(*args, **kwargs):
        return {"roles": ["Admin"]}

    monkeypatch.setattr(auth, "parse_token", mock_parse_token)
    client = TestClient(app)
    response = client.post("/proposal/submit", headers={"Authorization": "Bearer abcd"})
    assert response.status_code == 422
