from unittest.mock import patch
import pytest
from zoneinfo import ZoneInfo
from http import HTTPStatus
from itertools import product
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
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.INTERNAL_SERVER_ERROR, None, None), config_file=CONFIG_FILE)
    ts = curve_class(dummy_curve_id, metadata=None, session=mock_session)

    # act & assert
    with pytest.raises(CurveException):
        _ = ts.get_data_range(*method_args)


@pytest.mark.parametrize(
    "curve_class, method_args, empty_status_code",
    [
        (TimeSeriesCurve, ["1024-05-08"], HTTPStatus.NO_CONTENT),
        (TimeSeriesCurve, ["1024-05-08"], HTTPStatus.NOT_FOUND),
        (TaggedInstanceCurve, ["2024-05-08", "1024-05-08"], HTTPStatus.NO_CONTENT),
        (TaggedInstanceCurve, ["2024-05-08", "1024-05-08"], HTTPStatus.NOT_FOUND),
        (TaggedCurve, ["1024-05-08"], HTTPStatus.NO_CONTENT),
        (TaggedCurve, ["1024-05-08"], HTTPStatus.NOT_FOUND),
        (InstanceCurve, ["2024-05-08", "1024-05-08"], HTTPStatus.NO_CONTENT),
        (InstanceCurve, ["2024-05-08", "1024-05-08"], HTTPStatus.NOT_FOUND)
    ]
)
def test_all_curve_types_get_data_range__empty(dummy_curve_id, curve_class, method_args, empty_status_code):
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(empty_status_code, None, None), config_file=CONFIG_FILE)
    ts = curve_class(dummy_curve_id, metadata=None, session=mock_session)

    # act & assert
    assert ts.get_data_range(*method_args) is None


# Define the classes and their URL bases
curve_info = [
    (InstanceCurve, "/api/instances/"),
    (TaggedCurve, "/api/series/tagged/"),
    (TaggedInstanceCurve, "/api/instances/tagged/"),
    (TimeSeriesCurve, "/api/series/")
]

# Define the range parameters
range_params = [
    ("2024-05-08T00:00:00+02:00", "2024-05-11T22:00:00+02:00"),
    (None, None)
]

@pytest.mark.parametrize(
    "CurveCls, url_base, range_begin, range_end",
    [
        (curve_cls, url, start, end)
        for (curve_cls, url), (start, end) in product(curve_info, range_params)
    ]
)
def test_get_data_range(dummy_curve_id, CurveCls, url_base, range_begin, range_end):
    # arrange
    param_from = "2024-05-03" 
    param_to = "2024-05-12"
    output_time_zone = "JST"
    issue_date = "2024-04-01"
    tag = "tag-123"
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.OK, range_begin, range_end), config_file=CONFIG_FILE)
    ts = CurveCls(dummy_curve_id, metadata=None, session=mock_session)
    
    url_part = url_base + f"{dummy_curve_id}/range"
    
    # act
    if CurveCls == InstanceCurve:
        range = ts.get_data_range(issue_date, param_from, param_to, output_time_zone)
    elif CurveCls == TaggedCurve:
        range = ts.get_data_range(tag, param_from, param_to, output_time_zone)
    elif CurveCls == TaggedInstanceCurve:
        range = ts.get_data_range(issue_date, tag, param_from, param_to, output_time_zone)
    else:
        range = ts.get_data_range(param_from, param_to, output_time_zone)

    # assert
    tz = ZoneInfo("Asia/Tokyo")
    if CurveCls == InstanceCurve:
        assert mock_session.call_args == ["GET", "rtsp://test.host", f"{url_part}?issue_date={issue_date}&from={param_from}&to={param_to}"]
    elif CurveCls == TaggedCurve:
        assert mock_session.call_args == ["GET", "rtsp://test.host", f"{url_part}?tag={tag}&from={param_from}&to={param_to}"]
    elif CurveCls == TaggedInstanceCurve:
        assert mock_session.call_args == ["GET", "rtsp://test.host", f"{url_part}?issue_date={issue_date}&tag={tag}&from={param_from}&to={param_to}"]
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
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.INTERNAL_SERVER_ERROR, None, None), config_file=CONFIG_FILE)
    ts = CurveCls(dummy_curve_id, metadata=None, session=mock_session)

    # act & assert
    with pytest.raises(ValueError):
        _ = ts.get_data_range(issue_date=None)


@pytest.fixture
def dummy_curve_id():
    return 123
