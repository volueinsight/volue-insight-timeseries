import json
import os

import pytest
import requests_mock

from volue_insight_timeseries.util import TIME_SERIES, TS
import volue_insight_timeseries as vit

authprefix = 'rtsp://auth.host/oauth2'
prefix = 'rtsp://test.host/api'


#
# Fixtures of dummy input data which is not important
#

@pytest.fixture
def dummy_issue_date() -> str:
    return "2024-05-08T00:00:00+02:00"


@pytest.fixture
def dummy_curve_id() -> int:
    return 123

#
# Fixtures of timeseries outputs used in tests
#

@pytest.fixture
def ts1():
    points = [[0, 80], [2678400000, 90],
              [5097600000, 70], [7776000000, 120]]
    return TS(id=1, name='This is a Name', frequency='M', time_zone='CET',
              curve_type=TIME_SERIES, points=points)


@pytest.fixture
def ts2():
    points = [[0, 120], [2678400000, 210],
              [5097600000, 330], [7776000000, 380]]
    return TS(id=2, name='This is another Name', frequency='M',
              time_zone='CET', curve_type=TIME_SERIES, points=points)


@pytest.fixture
def ts3():
    points = [[0, 220], [2678400000, 120],
              [5097600000, 140], [7776000000, 580]]
    return TS(id=3, name='This is a third Name', frequency='M',
              time_zone='CET', curve_type=TIME_SERIES, points=points)


@pytest.fixture
def ts4():
    points = [
        [2153343600000, 10],
        [2153426400000, 20],
        [2153512800000, 30]
    ]
    return TS(id=4, name='Test 2038 issue', frequency='D',
              time_zone='CET', curve_type=TIME_SERIES, points=points)


@pytest.fixture
def ts5():
    points = [[0, 220]]
    return TS(id=5, name='Test frequency', frequency='D',
              time_zone='CET', curve_type=TIME_SERIES, points=points)


#
# Fixtures to set up the session for the rest of the tests
# Returns both a session and a request mock linked into the session.
#

@pytest.fixture
def session() -> tuple[vit.Session, requests_mock.Adapter]:
    config_file = os.path.join(os.path.dirname(__file__), 'testconfig_oauth.ini')
    s = vit.Session()
    mock = requests_mock.Adapter()
    s._session.mount('rtsp', mock)
    client_token = json.dumps({'token_type': 'Bearer', 'access_token': 'secrettoken',
                               'expires_in': 1000})
    mock.register_uri('POST', authprefix + '/token', text=client_token)
    s.read_config_file(config_file)
    return s, mock


@pytest.fixture
def ts_curve(session) -> tuple[vit.curves.TimeSeriesCurve, vit.Session, requests_mock.Adapter]:
    s, m = session
    metadata = {'id': 5, 'name': 'testcurve5',
                'frequency': 'H', 'time_zone': 'CET',
                'curve_type': 'TIME_SERIES'}
    m.register_uri('GET', prefix + '/curves/get?name=testcurve5', text=json.dumps(metadata))
    c: vit.curves.TimeSeriesCurve = s.get_curve(name='testcurve5')
    return c, s, m


@pytest.fixture
def tagged_curve(session) -> tuple[vit.curves.TaggedCurve, vit.Session, requests_mock.Adapter]:
    s, m = session
    metadata = {'id': 9, 'name': 'testcurve9',
                'frequency': 'H', 'time_zone': 'CET',
                'curve_type': 'TAGGED'}
    m.register_uri('GET', prefix + '/curves/get?name=testcurve9', text=json.dumps(metadata))
    c: vit.curves.TaggedCurve = s.get_curve(name='testcurve9')
    return c, s, m


@pytest.fixture
def inst_curve(session) -> tuple[vit.curves.InstanceCurve, vit.Session, requests_mock.Adapter]:
    s, m = session
    metadata = {'id': 7, 'name': 'testcurve7',
                'frequency': 'D', 'time_zone': 'CET',
                'curve_type': 'INSTANCES'}
    m.register_uri('GET', prefix + '/curves/get?name=testcurve7', text=json.dumps(metadata))
    c: vit.curves.InstanceCurve = s.get_curve(name='testcurve7')
    return c, s, m


@pytest.fixture
def tagged_inst_curve(session) -> tuple[vit.curves.TaggedInstanceCurve, vit.Session, requests_mock.Adapter]:
    s, m = session
    metadata = {'id': 10, 'name': 'testcurve10',
                'frequency': 'D', 'time_zone': 'CET',
                'curve_type': 'TAGGED_INSTANCES'}
    m.register_uri('GET', prefix + '/curves/get?name=testcurve10', text=json.dumps(metadata))
    c: vit.curves.TaggedInstanceCurve = s.get_curve(name='testcurve10')
    return c, s, m
