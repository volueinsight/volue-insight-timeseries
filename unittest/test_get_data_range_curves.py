from unittest.mock import patch
import pytest
from zoneinfo import ZoneInfo
from http import HTTPStatus
from volue_insight_timeseries.util import Range, CurveException
from volue_insight_timeseries.curves import InstanceCurve, TaggedCurve, TaggedInstanceCurve, TimeSeriesCurve

from helper.common import CONFIG_FILE
from helper.mock import RangeResponseMock, SessionMock


@pytest.mark.parametrize("range_begin,range_end", [("2024-05-08T00:00:00+02:00", "2024-05-11T22:00:00+02:00"), (None, None)])
def test_instance_curve_get_data_range(dummy_curve_id, range_begin, range_end):
    # arrange
    param_from = "2024-05-03" 
    param_to = "2024-05-12"
    issue_date = "2024-04-01"
    output_time_zone = "JST"
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.OK, range_begin, range_end), config_file=CONFIG_FILE)
    ts = InstanceCurve(dummy_curve_id, metadata=None, session=mock_session)

    # act
    range = ts.get_data_range(issue_date, param_from, param_to, output_time_zone)

    # assert
    tz = ZoneInfo("Asia/Tokyo")
    assert mock_session.call_args == ["GET", "rtsp://test.host", f"/api/instances/{dummy_curve_id}/range?issue_date={issue_date}&from={param_from}&to={param_to}"]
    assert range.begin == Range.parse_datetime(range_begin, tz)
    assert range.end == Range.parse_datetime(range_end, tz)


def test_instance_curve_get_data_range__exception(dummy_curve_id):
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.INTERNAL_SERVER_ERROR, None, None), config_file=CONFIG_FILE)
    ts = InstanceCurve(dummy_curve_id, metadata=None, session=mock_session)

    # act & assert
    with pytest.raises(CurveException):
        _ = ts.get_data_range("2024-05-08")


@pytest.mark.parametrize("empty_status_code", [HTTPStatus.NO_CONTENT, HTTPStatus.NOT_FOUND])
def test_instance_curve_get_data_range__empty(dummy_curve_id, empty_status_code):
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(empty_status_code, None, None), config_file=CONFIG_FILE)
    ts = InstanceCurve(dummy_curve_id, metadata=None, session=mock_session)

    # act & assert
    assert ts.get_data_range("2024-05-08", date_to="1024-05-08") is None


@pytest.mark.parametrize("range_begin,range_end", [("2024-05-08T00:00:00+02:00", "2024-05-11T22:00:00+02:00"), (None, None)])
def test_tagged_curve_get_data_range(dummy_curve_id, range_begin, range_end):
    # arrange
    param_from = "2024-05-03" 
    param_to = "2024-05-12"
    tag = "tag-123"
    output_time_zone = "JST"
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.OK, range_begin, range_end), config_file=CONFIG_FILE)
    ts = TaggedCurve(dummy_curve_id, metadata=None, session=mock_session)

    # act
    range = ts.get_data_range(tag, param_from, param_to, output_time_zone)

    # assert
    tz = ZoneInfo("Asia/Tokyo")
    assert mock_session.call_args == ["GET", "rtsp://test.host", f"/api/series/tagged/{dummy_curve_id}/range?tag={tag}&from={param_from}&to={param_to}"]
    assert range.begin == Range.parse_datetime(range_begin, tz)
    assert range.end == Range.parse_datetime(range_end, tz)


def test_tagged_curve_get_data_range__exception(dummy_curve_id):
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.INTERNAL_SERVER_ERROR, None, None), config_file=CONFIG_FILE)
    ts = TaggedCurve(dummy_curve_id, metadata=None, session=mock_session)

    # act & assert
    with pytest.raises(CurveException):
        _ = ts.get_data_range()


@pytest.mark.parametrize("empty_status_code", [HTTPStatus.NO_CONTENT, HTTPStatus.NOT_FOUND])
def test_tagged_curve_get_data_range__empty(dummy_curve_id, empty_status_code):
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(empty_status_code, None, None), config_file=CONFIG_FILE)
    ts = TaggedCurve(dummy_curve_id, metadata=None, session=mock_session)

    # act & assert
    assert ts.get_data_range(date_to="1024-05-08") is None


@pytest.mark.parametrize("range_begin,range_end", [("2024-05-08T00:00:00+02:00", "2024-05-11T22:00:00+02:00"), (None, None)])
def test_tagged_instance_curve_get_data_range(dummy_curve_id, range_begin, range_end):
    # arrange
    tag = "tag-123"
    param_from = "2024-05-03" 
    param_to = "2024-05-12"
    output_time_zone = "JST"
    issue_date = "2024-04-01"

    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.OK, range_begin, range_end), config_file=CONFIG_FILE)
    ts = TaggedInstanceCurve(dummy_curve_id, metadata=None, session=mock_session)

    # act
    range = ts.get_data_range(issue_date, tag, param_from, param_to, output_time_zone)

    # assert
    tz = ZoneInfo("Asia/Tokyo")
    assert mock_session.call_args == ["GET", "rtsp://test.host", f"/api/instances/tagged/{dummy_curve_id}/range?issue_date={issue_date}&tag={tag}&from={param_from}&to={param_to}"]
    assert range.begin == Range.parse_datetime(range_begin, tz)
    assert range.end == Range.parse_datetime(range_end, tz)


def test_tagged_instance_curve_get_data_range__exception(dummy_curve_id):
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.INTERNAL_SERVER_ERROR, None, None), config_file=CONFIG_FILE)
    ts = TaggedInstanceCurve(dummy_curve_id, metadata=None, session=mock_session)

    # act & assert
    with pytest.raises(CurveException):
        _ = ts.get_data_range("2024-05-08")


@pytest.mark.parametrize("empty_status_code", [HTTPStatus.NO_CONTENT, HTTPStatus.NOT_FOUND])
def test_tagged_instance_curve_get_data_range__empty(dummy_curve_id, empty_status_code):
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(empty_status_code, None, None), config_file=CONFIG_FILE)
    ts = TaggedInstanceCurve(dummy_curve_id, metadata=None, session=mock_session)

    # act & assert
    assert ts.get_data_range("2024-05-08", date_to="1024-05-08") is None


@pytest.mark.parametrize("range_begin,range_end", [("2024-05-08T00:00:00+02:00", "2024-05-11T22:00:00+02:00"), (None, None)])
def test_timeseries_curve_get_data_range(dummy_curve_id, range_begin, range_end):
    # arrange
    param_from = "2024-05-03" 
    param_to = "2024-05-12"
    output_time_zone = "JST"
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.OK, range_begin, range_end), config_file=CONFIG_FILE)
    ts = TimeSeriesCurve(dummy_curve_id, metadata=None, session=mock_session)

    # act
    range = ts.get_data_range(param_from, param_to, output_time_zone)

    # assert
    tz = ZoneInfo("Asia/Tokyo")
    assert mock_session.call_args == ["GET", "rtsp://test.host", f"/api/series/{dummy_curve_id}/range?from={param_from}&to={param_to}"]
    assert range.begin == Range.parse_datetime(range_begin, tz)
    assert range.end == Range.parse_datetime(range_end, tz)


def test_timeseries_curve_get_data_range__exception(dummy_curve_id):
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.INTERNAL_SERVER_ERROR, None, None), config_file=CONFIG_FILE)
    ts = TimeSeriesCurve(dummy_curve_id, metadata=None, session=mock_session)

    # act & assert
    with pytest.raises(CurveException):
        _ = ts.get_data_range()


@pytest.mark.parametrize("empty_status_code", [HTTPStatus.NO_CONTENT, HTTPStatus.NOT_FOUND])
def test_timeseries_curve_get_data_range__empty(dummy_curve_id, empty_status_code):
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(empty_status_code, None, None), config_file=CONFIG_FILE)
    ts = TimeSeriesCurve(dummy_curve_id, metadata=None, session=mock_session)

    # act & assert
    assert ts.get_data_range(date_to="1024-05-08") is None


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