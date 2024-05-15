import json

import volue_insight_timeseries as vit
from unittest.mock import patch
from urllib.parse import quote_plus
import pandas as pd
import pytest
from zoneinfo import ZoneInfo
from http import HTTPStatus
from datetime import datetime, timedelta
from itertools import product
from pathlib import Path

from typing import Optional

prefix = 'rtsp://test.host/api'
authprefix = 'rtsp://auth.host/oauth2'

CONFIG_FILE = Path(__file__).parent.resolve() / "testconfig_key.ini"


class RangeResponseMock:
    def __init__(self, status_code: HTTPStatus, range_begin: Optional[str], range_end: Optional[str]):
        self.range_resp = {"begin": range_begin, "end": range_end}
        self.status_code = status_code
        self.content = b""

    def json(self) -> dict:
        return self.range_resp


class SessionMock(vit.Session):
    def __init__(self, resp, **kwargs):
        super().__init__(**kwargs)
        self.resp = resp
        self.call_args = []

    def data_request(self, req_type, urlbase, url, **kwargs):
        self.call_args = [req_type, urlbase, url]
        return self.resp


#
# Test the various authorization headers
#

def test_login_header(session):
    s, m = session
    m.register_uri('GET', prefix + '/units', text='{"res": "ok"}',
                   request_headers={'Authorization': '{} {}'.format(s.auth.token_type,
                                                                    s.auth.token)})
    r = s.get_attribute('units')
    assert r['res'] == 'ok'


#
# Test curves
#

def test_search(session):
    s, m = session
    metadata = [{'id': 5, 'name': 'testcurve5',
                 'frequency': 'H', 'time_zone': 'CET',
                 'curve_type': 'TIME_SERIES'},
                {'id': 6, 'name': 'testcurve6',
                 'frequency': 'D', 'time_zone': 'CET',
                 'curve_type': 'INSTANCES'}]
    m.register_uri('GET', prefix + '/curves?name=testcurve5&name=testcurve6', text=json.dumps(metadata))
    c = s.search(name=['testcurve5', 'testcurve6'])
    assert len(c) == 2
    assert isinstance(c[0], vit.curves.TimeSeriesCurve)
    assert isinstance(c[1], vit.curves.InstanceCurve)


def test_time_series(ts_curve):
    c, s, m = ts_curve
    assert isinstance(c, vit.curves.TimeSeriesCurve)
    assert c.id == 5
    assert c.name == 'testcurve5'
    assert c.frequency == 'H'
    assert c.time_zone == 'CET'


def test_ts_data(ts_curve):
    c, s, m = ts_curve
    datapoints = {'id': 5, 'frequency': 'H', 'points': [[140000000000, 10.0]]}
    m.register_uri('GET', prefix + '/series/5?from=1&to=2', text=json.dumps(datapoints))
    d = c.get_data(data_from=1, data_to=2)
    assert isinstance(d, vit.util.TS)
    assert d.frequency == 'H'


def test_tagged(tagged_curve):
    c, s, m = tagged_curve
    assert isinstance(c, vit.curves.TaggedCurve)
    assert c.id == 9
    assert c.name == 'testcurve9'
    assert c.frequency == 'H'
    assert c.time_zone == 'CET'


def test_tagged_tags(tagged_curve):
    c, s, m = tagged_curve
    tags = {'test': 'ok'}
    m.register_uri('GET', prefix + '/series/tagged/9/tags', text=json.dumps(tags))
    res = c.get_tags()
    assert res['test'] == 'ok'


def test_tagged_data(tagged_curve):
    c, s, m = tagged_curve
    datapoints = [{'id': 9, 'tag': 'tag1', 'frequency': 'H', 'points': [[140000000000, 10.0]]}]
    m.register_uri('GET', prefix + '/series/tagged/9?tag=tag1', text=json.dumps(datapoints))
    d = c.get_data(tag='tag1')
    assert isinstance(d, vit.util.TS)
    assert d.frequency == 'H'
    assert d.tag == 'tag1'


def test_inst_curve(inst_curve):
    c, s, m = inst_curve
    assert isinstance(c, vit.curves.InstanceCurve)
    assert c.id == 7
    assert c.name == 'testcurve7'
    assert c.frequency == 'D'
    assert c.time_zone == 'CET'


def test_inst_search(inst_curve):
    c, s, m = inst_curve
    search_data = [
        {'frequency': 'H', 'points': [[140000000000, 10.0]],
         'name': 'inst_name', 'id': 10,
         'issue_date': '46'},
        {'frequency': 'H', 'points': [[140000000000, 10.0]],
         'name': 'inst_name', 'id': 10,
         'issue_date': '50'}]
    m.register_uri('GET', prefix + '/instances/7?issue_date=46&issue_date=50',
                   text=json.dumps(search_data))
    res = c.search_instances(issue_dates=['46', '50'])
    assert len(res) == 2


def test_inst_get_instance(inst_curve):
    c, s, m = inst_curve
    inst = {'frequency': 'H', 'points': [[140000000000, 10.0]],
            'name': 'inst_name', 'id': 7,
            'issue_date': '2016-01-01T00:00Z'}
    m.register_uri('GET',
                   prefix + '/instances/7/get?issue_date=2016-01-01T00:00Z&with_data=true',
                   text=json.dumps(inst))
    res = c.get_instance(issue_date='2016-01-01T00:00Z')
    assert isinstance(res, vit.util.TS)
    assert res.frequency == 'H'
    assert res.name == 'inst_name'


def test_inst_get_latest(inst_curve):
    c, s, m = inst_curve
    inst = {'frequency': 'H', 'points': [[140000000000, 10.0]],
            'name': 'inst_name', 'id': 7,
            'issue_date': '2016-01-01T00:00Z'}
    m.register_uri('GET', prefix + '/instances/7/latest?with_data=false&issue_date=56',
                   text=json.dumps(inst))
    res = c.get_latest(issue_dates=56, with_data=False)
    assert isinstance(res, vit.util.TS)
    assert res.frequency == 'H'
    assert res.name == 'inst_name'


def test_inst_get_relative(inst_curve):
    c, s, m = inst_curve
    inst = {'frequency': 'H', 'points': [[140000000000, 10.0]],
            'name': 'inst_name', 'id': 7}
    m.register_uri('GET', prefix + '/instances/7/relative?data_offset=PT1H&issue_date_from=2016-01-01' +
                   '&issue_date_to=2016-02-01&data_max_length=PT1H',
                   text=json.dumps(inst))
    res = c.get_relative(data_offset='PT1H', data_max_length='PT1H', issue_date_from='2016-01-01',
                         issue_date_to='2016-02-01')
    assert isinstance(res, vit.util.TS)
    assert res.frequency == 'H'
    assert res.name == 'inst_name'


def test_inst_get_absolute(inst_curve):
    c, s, m = inst_curve
    inst = {'frequency': 'H', 'points': [[140000000000, 10.0]],
            'name': 'inst_name', 'id': 7}
    m.register_uri('GET', prefix + '/instances/7/absolute?data_date=2016-01-01T12:00&issue_frequency=H' +
                   '&issue_date_from=2016-01-01&issue_date_to=2016-02-01',
                   text=json.dumps(inst))
    res = c.get_absolute(data_date='2016-01-01T12:00', issue_frequency='H', issue_date_from='2016-01-01',
                         issue_date_to='2016-02-01')
    assert isinstance(res, vit.util.TS)
    assert res.frequency == 'H'
    assert res.name == 'inst_name'


def test_tagged_inst_curve(tagged_inst_curve):
    c, s, m = tagged_inst_curve
    assert isinstance(c, vit.curves.TaggedInstanceCurve)
    assert c.id == 10
    assert c.name == 'testcurve10'
    assert c.frequency == 'D'
    assert c.time_zone == 'CET'


def test_tagged_inst_tags(tagged_inst_curve):
    c, s, m = tagged_inst_curve
    tags = {'test': 'ok'}
    m.register_uri('GET', prefix + '/instances/tagged/10/tags', text=json.dumps(tags))
    res = c.get_tags()
    assert res['test'] == 'ok'


def test_tagged_inst_search(tagged_inst_curve):
    c, s, m = tagged_inst_curve
    search_data = [
        {'frequency': 'H', 'points': [[140000000000, 10.0]],
         'name': 'inst_name', 'id': 10, 'tag': 'tag1',
         'issue_date': '46'},
        {'frequency': 'H', 'points': [[140000000000, 10.0]],
         'name': 'inst_name', 'id': 10, 'tag': 'tag1',
         'issue_date': '50'}]
    m.register_uri('GET', prefix + '/instances/tagged/10?tag=tag1&issue_date=46&issue_date=50',
                   text=json.dumps(search_data))
    res = c.search_instances(tags='tag1', issue_dates=['46', '50'])
    assert len(res) == 2


def test_tagged_inst_get_instance(tagged_inst_curve):
    c, s, m = tagged_inst_curve
    inst = [{'frequency': 'H', 'points': [[140000000000, 10.0]],
             'name': 'inst_name', 'id': 10, 'tag': 'tag1',
             'issue_date': '2016-01-01T00:00Z'}]
    m.register_uri('GET',
                   prefix + '/instances/tagged/10/get?tag=tag1&issue_date=2016-01-01T00:00Z&with_data=true',
                   text=json.dumps(inst))
    res = c.get_instance(tag='tag1', issue_date='2016-01-01T00:00Z')
    assert isinstance(res, vit.util.TS)
    assert res.frequency == 'H'
    assert res.name == 'inst_name'
    assert res.tag == 'tag1'


def test_tagged_inst_get_latest(tagged_inst_curve):
    c, s, m = tagged_inst_curve
    inst = {'frequency': 'H', 'points': [[140000000000, 10.0]],
            'name': 'inst_name', 'id': 10, 'tag': 'tag1',
            'issue_date': '2016-01-01T00:00Z'}
    m.register_uri('GET', prefix + '/instances/tagged/10/latest?with_data=false&issue_date=56',
                   text=json.dumps(inst))
    res = c.get_latest(issue_dates=56, with_data=False)
    assert isinstance(res, vit.util.TS)
    assert res.frequency == 'H'
    assert res.name == 'inst_name'
    assert res.tag == 'tag1'


def test_tagged_inst_get_relative(tagged_inst_curve):
    c, s, m = tagged_inst_curve
    inst = {'frequency': 'H', 'points': [[140000000000, 10.0]],
            'name': 'inst_name', 'id': 10, 'tag': 'tag1'}
    m.register_uri('GET', prefix + '/instances/tagged/10/relative?data_offset=PT1H&issue_date_from=2016-01-01' +
                   '&issue_date_to=2016-02-01&data_max_length=PT1H&tag=tag1',
                   text=json.dumps(inst))
    res = c.get_relative(data_offset='PT1H', data_max_length='PT1H', issue_date_from='2016-01-01',
                         issue_date_to='2016-02-01', tag='tag1')
    assert isinstance(res, vit.util.TS)
    assert res.frequency == 'H'
    assert res.name == 'inst_name'
    assert res.tag == 'tag1'


def test_tagged_inst_get_absolute(tagged_inst_curve):
    c, s, m = tagged_inst_curve
    inst = {'frequency': 'H', 'points': [[140000000000, 10.0]],
            'name': 'inst_name', 'id': 10, 'tag': 'tag1'}
    m.register_uri('GET', prefix + '/instances/tagged/10/absolute?data_date=2016-01-01T12:00&issue_frequency=H' +
                   '&tag=tag1&issue_date_from=2016-01-01&issue_date_to=2016-02-01',
                   text=json.dumps(inst))
    res = c.get_absolute(data_date='2016-01-01T12:00', issue_frequency='H', issue_date_from='2016-01-01',
                         issue_date_to='2016-02-01', tag='tag1')
    assert isinstance(res, vit.util.TS)
    assert res.frequency == 'H'
    assert res.name == 'inst_name'
    assert res.tag == 'tag1'
