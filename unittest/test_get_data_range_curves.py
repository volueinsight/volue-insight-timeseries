from unittest.mock import patch
from urllib.parse import quote_plus
import pandas as pd
import pytest
from zoneinfo import ZoneInfo
from http import HTTPStatus
from datetime import datetime, timedelta
from itertools import product
from pathlib import Path
from volue_insight_timeseries.session import Session
from volue_insight_timeseries.util import Range, CurveException
from volue_insight_timeseries.curves import InstanceCurve, TaggedCurve, TaggedInstanceCurve, TimeSeriesCurve

from helper.common import CONFIG_FILE
from helper.mock import RangeResponseMock, SessionMock


@pytest.mark.parametrize(
    "curve_class, method_args",
    [
        (InstanceCurve, ["2024-05-08"]),
        (TaggedCurve, []),
        (TaggedInstanceCurve, ["2024-05-08"]),
        (TimeSeriesCurve, [])
    ]
)
def test_all_curve_types_get_data_range__exception(dummy_curve_id, curve_class, method_args):
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.INTERNAL_SERVER_ERROR, None, None),
                               config_file=CONFIG_FILE)
    ts = curve_class(dummy_curve_id, metadata=None, session=mock_session)

    # act & assert
    with pytest.raises(CurveException):
        _ = ts.get_data_range(*method_args)


empty_curve_info = [
    (TimeSeriesCurve, {"date_to": "1024-05-08"}),
    (TaggedInstanceCurve, {"issue_date": "2024-05-08T00:00:00+02:00", "tag": None, "date_to": "1024-05-08"}),
    (TaggedCurve, {"tag": None, "date_to": "1024-05-08"}),
    (InstanceCurve, {"issue_date": "2024-05-08T00:00:00+02:00", "date_to": "1024-05-08"})
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
    (InstanceCurve, "/api/instances/", {"issue_date": "2024-05-08T00:00:00+02:00"}),
    (TaggedCurve, "/api/series/tagged/", {"tag": "tag-123"}),
    (TaggedInstanceCurve, "/api/instances/tagged/", {"issue_date": "2024-05-08T00:00:00+02:00", "tag": "tag-123"}),
    (TimeSeriesCurve, "/api/series/", {})
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
    if CurveCls == InstanceCurve:
        assert mock_session.call_args == ["GET", "rtsp://test.host",
                                          f"{url_part}?issue_date={quote_plus(dummy_issue_date)}&from={param_from}&to={param_to}"]
    elif CurveCls == TaggedCurve:
        assert mock_session.call_args == ["GET", "rtsp://test.host",
                                          f"{url_part}?tag={tag}&from={param_from}&to={param_to}"]
    elif CurveCls == TaggedInstanceCurve:
        assert mock_session.call_args == ["GET", "rtsp://test.host",
                                          f"{url_part}?issue_date={quote_plus(dummy_issue_date)}&tag={tag}&from={param_from}&to={param_to}"]
    else:
        assert mock_session.call_args == ["GET", "rtsp://test.host", f"{url_part}?from={param_from}&to={param_to}"]

    assert range.begin == Range.parse_datetime(range_begin, tz)
    assert range.end == Range.parse_datetime(range_end, tz)


@patch("volue_insight_timeseries.curves.InstanceCurve.get_issue_dates")
@patch("volue_insight_timeseries.curves.InstanceCurve.get_data_range")
def test_instance_curve_get_curve_data_range(get_data_range_mock, get_issue_dates_mock, dummy_curve_id):
    # arrange
    expected_begin, expected_end = "2024-05-08T00:00:00+02:00", "2024-05-13T00:00:00+02:00"
    data_range_dict = {
        # issue date -> data range
        "2024-05-09T00:00:00+02:00": Range("2024-05-10T00:00:00+02:00", expected_end),
        "2024-05-08T00:00:00+02:00": Range("2024-05-09T00:00:00+02:00", "2024-05-12T00:00:00+02:00"),
        "2024-05-07T00:00:00+02:00": Range(expected_begin, "2024-05-11T00:00:00+02:00"),
    }
    get_issue_dates_mock.return_value = list(data_range_dict.keys())
    get_data_range_mock.side_effect = lambda x: data_range_dict[x]

    ts = InstanceCurve(dummy_curve_id, metadata=None, session=None)

    # act
    range = ts.get_curve_data_range()

    # assert
    assert range == Range(expected_begin, expected_end)


@pytest.mark.parametrize("CurveCls", [InstanceCurve, TaggedInstanceCurve])
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

    read_session = Session(config_file=wapi_dev_config)
    test_curve = read_session.get_curve(name=curve_name)
    test_curve_data_range = test_curve.get_data_range(**kwargs)

    # Due to some test curves having "no data" only way to actually check correctness is to check for class type
    assert isinstance(test_curve_data_range, Range)


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

    read_session = Session(config_file=wapi_dev_config)
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

    read_session = Session(config_file=wapi_dev_config)
    test_curve = read_session.get_curve(name=curve_name)
    test_curve_data_range = test_curve.get_data_range(date_from=start_date, date_to=end_date)
    pytest.set_trace()
    assert test_curve_data_range is not None


@pytest.fixture
def dummy_issue_date():
    return "2024-05-08T00:00:00+02:00"


@pytest.fixture
def dummy_curve_id():
    return 123
