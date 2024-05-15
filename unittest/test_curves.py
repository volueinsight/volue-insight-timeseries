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


#
# Test get_data_range
#

@pytest.mark.parametrize(
    "curve_class, method_args",
    [
        (vit.curves.InstanceCurve, ["2024-05-08"]),
        (vit.curves.TaggedCurve, []),
        (vit.curves.TaggedInstanceCurve, ["2024-05-08"]),
        (vit.curves.TimeSeriesCurve, [])
    ]
)
def test_all_curve_types_get_data_range__exception(dummy_curve_id, curve_class, method_args):
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.INTERNAL_SERVER_ERROR, None, None),
                               config_file=CONFIG_FILE)
    ts = curve_class(dummy_curve_id, metadata=None, session=mock_session)

    # act & assert
    with pytest.raises(vit.util.CurveException):
        _ = ts.get_data_range(*method_args)


empty_curve_info = [
    (vit.curves.TimeSeriesCurve, {"date_to": "1024-05-08"}),
    (vit.curves.TaggedInstanceCurve, {"issue_date": "2024-05-08T00:00:00+02:00", "tag": None, "date_to": "1024-05-08"}),
    (vit.curves.TaggedCurve, {"tag": None, "date_to": "1024-05-08"}),
    (vit.curves.InstanceCurve, {"issue_date": "2024-05-08T00:00:00+02:00", "date_to": "1024-05-08"})
]

empty_status_codes = [HTTPStatus.NO_CONTENT, HTTPStatus.NOT_FOUND]


@pytest.mark.parametrize(
    "curve_class, method_kwargs, empty_status_code",
    [
        (curve_cls, kwargs, status_code)
        for (curve_cls, kwargs), status_code in product(empty_curve_info, empty_status_codes)
    ]
)
def test_all_curve_types_get_data_range__empty(dummy_curve_id, curve_class, method_kwargs, empty_status_code):
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(empty_status_code, None, None), config_file=CONFIG_FILE)
    ts = curve_class(dummy_curve_id, metadata=None, session=mock_session)

    # act & assert
    assert ts.get_data_range(**method_kwargs) is None


success_curve_info = [
    (vit.curves.InstanceCurve, "/api/instances/", {"issue_date": "2024-05-08T00:00:00+02:00"}),
    (vit.curves.TaggedCurve, "/api/series/tagged/", {"tag": "tag-123"}),
    (vit.curves.TaggedInstanceCurve, "/api/instances/tagged/",
     {"issue_date": "2024-05-08T00:00:00+02:00", "tag": "tag-123"}),
    (vit.curves.TimeSeriesCurve, "/api/series/", {})
]

success_range_params = [
    ("2024-05-07T00:00:00+02:00", "2024-05-11T22:00:00+02:00"),
    (None, None)
]


@pytest.mark.parametrize(
    "CurveCls, url_base, extra_kwargs, range_begin, range_end",
    [
        (curve_cls, url, extra_kwargs, start, end)
        for (curve_cls, url, extra_kwargs), (start, end) in product(success_curve_info, success_range_params)
    ]
)
def test_get_data_range(dummy_curve_id, dummy_issue_date, CurveCls, url_base, extra_kwargs, range_begin, range_end):
    # arrange
    param_from = "2024-05-03"
    param_to = "2024-05-12"
    output_time_zone = "JST"
    extra_kwargs.update(date_from=param_from, date_to=param_to, output_time_zone=output_time_zone)

    tag = "tag-123"
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.OK, range_begin, range_end), config_file=CONFIG_FILE)
    ts = CurveCls(dummy_curve_id, metadata=None, session=mock_session)

    url_part = url_base + f"{dummy_curve_id}/range"

    # act
    range = ts.get_data_range(**extra_kwargs)

    # assert
    tz = ZoneInfo("Asia/Tokyo")
    if CurveCls == vit.curves.InstanceCurve:
        assert mock_session.call_args == ["GET", "rtsp://test.host",
                                          f"{url_part}?issue_date={quote_plus(dummy_issue_date)}&from={param_from}&to={param_to}"]
    elif CurveCls == vit.curves.TaggedCurve:
        assert mock_session.call_args == ["GET", "rtsp://test.host",
                                          f"{url_part}?tag={tag}&from={param_from}&to={param_to}"]
    elif CurveCls == vit.curves.TaggedInstanceCurve:
        assert mock_session.call_args == ["GET", "rtsp://test.host",
                                          f"{url_part}?issue_date={quote_plus(dummy_issue_date)}&tag={tag}&from={param_from}&to={param_to}"]
    else:
        assert mock_session.call_args == ["GET", "rtsp://test.host", f"{url_part}?from={param_from}&to={param_to}"]

    assert range.begin == vit.util.Range.parse_datetime(range_begin, tz)
    assert range.end == vit.util.Range.parse_datetime(range_end, tz)


@patch("volue_insight_timeseries.curves.InstanceCurve.get_issue_dates")
@patch("volue_insight_timeseries.curves.InstanceCurve.get_data_range")
def test_instance_curve_get_curve_data_range(get_data_range_mock, get_issue_dates_mock, dummy_curve_id):
    # arrange
    expected_begin, expected_end = \
        datetime.fromisoformat("2024-05-08T00:00:00+02:00"), datetime.fromisoformat("2024-05-13T00:00:00+02:00")

    data_range_dict = {
        # issue date -> data range
        "2024-05-09T00:00:00+02:00": vit.util.Range(expected_end - timedelta(days=3), expected_end),
        "2024-05-08T00:00:00+02:00": vit.util.Range(expected_begin + timedelta(days=1),
                                                    expected_begin + timedelta(days=4)),
        "2024-05-07T00:00:00+02:00": vit.util.Range(expected_begin, expected_end + timedelta(days=3)),
    }
    get_issue_dates_mock.return_value = list(data_range_dict.keys())
    get_data_range_mock.side_effect = lambda x: data_range_dict[x]

    ts = vit.curves.InstanceCurve(dummy_curve_id, metadata=None, session=None)

    # act
    range = ts.get_curve_data_range()

    # assert
    assert range == vit.util.Range(expected_begin, expected_end)


@pytest.mark.parametrize("CurveCls", [vit.curves.InstanceCurve, vit.curves.TaggedInstanceCurve])
def test_instance_type_curves_raise_exception_on_invalid_issue_date(dummy_curve_id, CurveCls):
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.INTERNAL_SERVER_ERROR, None, None),
                               config_file=CONFIG_FILE)
    ts = CurveCls(dummy_curve_id, metadata=None, session=mock_session)

    # act & assert
    with pytest.raises(ValueError):
        _ = ts.get_data_range(issue_date=None)


@pytest.mark.skip("Integration tests. For local use only")
@pytest.mark.parametrize(
    "curve_name,kwargs",
    [
        (r"cc ch zurich test % cet h s", {}),
        (r"rdl dk test ec00 02 mwh/h cet min15 f", {"issue_date": "2024-05-05T00:00:00+02:00"}),
        (r"pri de intraday €/mwh cet h f", {"issue_date": "2024-05-05T09:15:00+02:00"})
    ]
)
def test_integration_all_curve_types_get_data_range(curve_name, kwargs):
    wapi_dev_config = Path("<path/to/your/credentials>")

    read_session = vit.Session(config_file=wapi_dev_config)
    test_curve = read_session.get_curve(name=curve_name)
    test_curve_data_range = test_curve.get_data_range(**kwargs)

    # Due to some test curves having "no data" only way to actually check correctness is to check for class type
    assert isinstance(test_curve_data_range, vit.util.Range)


@pytest.mark.skip("Integration tests. For local use only")
@pytest.mark.parametrize(
    "curve_name,kwargs",
    [
        (r"rdl dk test ec00 02 mwh/h cet min15 f", {"issue_date": (datetime.now() + timedelta(days=30)).isoformat()}),
        (r"pri de intraday €/mwh cet h f", {"issue_date": (datetime.now() + timedelta(days=30)).isoformat()})
    ]
)
def test_integration_future_issue_fail_get_data_range(curve_name, kwargs):
    wapi_dev_config = Path("<path/to/your/credentials>")

    read_session = vit.Session(config_file=wapi_dev_config)
    test_curve = read_session.get_curve(name=curve_name)
    test_curve_data_range = test_curve.get_data_range(**kwargs)
    assert test_curve_data_range is None


date_param_types = [
    ("2024-05-05", "2024-05-10"),
    ("2024-05-05T00:00:00+02:00", "2024-05-15T00:00:00+02:00"),
    (pd.Timestamp("2024-05-05T00:00:00+02:00"), pd.Timestamp("2024-05-15T00:00:00+02:00")),
    (datetime(2024, 5, 5, 0, 0, 0), datetime(2024, 5, 15, 0, 0, 0))
]


@pytest.mark.skip("Integration tests. For local use only")
@pytest.mark.parametrize(
    "curve_name, start_date, end_date",
    [
        (curve_name, start_date, end_date)
        for curve_name, (start_date, end_date) in product((r"cc ch zurich test % cet h s",), date_param_types)
    ]
)
def test_integration_different_data_types_get_data_range(curve_name, start_date, end_date):
    wapi_dev_config = Path("<path/to/your/credentials>")

    read_session = vit.Session(config_file=wapi_dev_config)
    test_curve = read_session.get_curve(name=curve_name)
    test_curve_data_range = test_curve.get_data_range(date_from=start_date, date_to=end_date)
    pytest.set_trace()
    assert test_curve_data_range is not None
