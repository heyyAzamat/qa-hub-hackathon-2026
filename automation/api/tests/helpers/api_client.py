"""
Thin wrapper around requests.Session.
Returns raw Response objects — assertions are kept in test files.
"""
from typing import Optional
import requests


class APIClient:
    def __init__(self, base_url: str, auth: Optional[tuple] = None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        if auth:
            self.session.auth = auth

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def get(self, path: str, **kwargs) -> requests.Response:
        return self.session.get(self._url(path), **kwargs)

    def post(self, path: str, json=None, **kwargs) -> requests.Response:
        return self.session.post(self._url(path), json=json, **kwargs)

    def put(self, path: str, json=None, **kwargs) -> requests.Response:
        return self.session.put(self._url(path), json=json, **kwargs)

    def patch(self, path: str, json=None, **kwargs) -> requests.Response:
        return self.session.patch(self._url(path), json=json, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.session.delete(self._url(path), **kwargs)

    def check_health(self) -> bool:
        """Returns True if the server is reachable."""
        try:
            r = self.session.get(self._url("/api/part/"), timeout=5)
            return r.status_code < 500
        except requests.exceptions.ConnectionError:
            return False
