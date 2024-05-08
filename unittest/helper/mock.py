from volue_insight_timeseries import Session
from typing import Optional
from http import HTTPStatus


class RangeResponseMock:
    def __init__(self, status_code: HTTPStatus, range_begin: Optional[str], range_end: Optional[str]):
        self.range_resp = {"begin": range_begin, "end": range_end}
        self.status_code = status_code
        self.content = b""
    
    def json(self) -> dict:
        return self.range_resp


class SessionMock(Session):
    def __init__(self, resp, **kwargs):
        super().__init__(**kwargs)
        self.resp = resp
        self.call_args = []

    def data_request(self, req_type, urlbase, url, **kwargs):
        self.call_args = [req_type, urlbase, url]
        return self.resp
