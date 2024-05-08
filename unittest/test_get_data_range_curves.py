import pytest
from zoneinfo import ZoneInfo
from http import HTTPStatus
from volue_insight_timeseries.util import Range, CurveException
from volue_insight_timeseries.curves import InstanceCurve, TaggedCurve, TaggedInstanceCurve, TimeSeriesCurve

from helper.common import CONFIG_FILE
from helper.mock import RangeResponseMock, SessionMock


@pytest.mark.parametrize("range_begin,range_end", [("2024-05-08T00:00:00+02:00", "2024-05-11T22:00:00+02:00"), (None, None)])
def test_instance_curve_get_data_range(range_begin, range_end):
    # arrange
    curve_id = 1234
    param_from = "2024-05-03" 
    param_to = "2024-05-12"
    issue_date = "2024-04-01"
    output_time_zone = "JST"
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.OK, range_begin, range_end), config_file=CONFIG_FILE)
    ts = InstanceCurve(curve_id, metadata=None, session=mock_session)

    # act
    range = ts.get_data_range(issue_date, param_from, param_to, output_time_zone)

    # assert
    tz = ZoneInfo("Asia/Tokyo")
    assert mock_session.call_args == ["GET", "rtsp://test.host", f"/api/instances/{curve_id}/range?issue_date={issue_date}&from={param_from}&to={param_to}"]
    assert range.begin == Range.parse_datetime(range_begin, tz)
    assert range.end == Range.parse_datetime(range_end, tz)


def test_instance_curve_get_data_range__exception():
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.INTERNAL_SERVER_ERROR, None, None), config_file=CONFIG_FILE)
    ts = InstanceCurve(123, metadata=None, session=mock_session)

    # act & assert
    with pytest.raises(CurveException):
        _ = ts.get_data_range("2024-05-08")


@pytest.mark.parametrize("empty_status_code", [HTTPStatus.NO_CONTENT, HTTPStatus.NOT_FOUND])
def test_instance_curve_get_data_range__empty(empty_status_code):
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(empty_status_code, None, None), config_file=CONFIG_FILE)
    ts = InstanceCurve(123, metadata=None, session=mock_session)

    # act & assert
    assert ts.get_data_range("2024-05-08", date_to="1024-05-08") is None


@pytest.mark.parametrize("range_begin,range_end", [("2024-05-08T00:00:00+02:00", "2024-05-11T22:00:00+02:00"), (None, None)])
def test_tagged_curve_get_data_range(range_begin, range_end):
    # arrange
    curve_id = 1234
    param_from = "2024-05-03" 
    param_to = "2024-05-12"
    tag = "tag-123"
    output_time_zone = "JST"
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.OK, range_begin, range_end), config_file=CONFIG_FILE)
    ts = TaggedCurve(curve_id, metadata=None, session=mock_session)

    # act
    range = ts.get_data_range(tag, param_from, param_to, output_time_zone)

    # assert
    tz = ZoneInfo("Asia/Tokyo")
    assert mock_session.call_args == ["GET", "rtsp://test.host", f"/api/series/tagged/{curve_id}/range?tag={tag}&from={param_from}&to={param_to}"]
    assert range.begin == Range.parse_datetime(range_begin, tz)
    assert range.end == Range.parse_datetime(range_end, tz)


def test_tagged_curve_get_data_range__exception():
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.INTERNAL_SERVER_ERROR, None, None), config_file=CONFIG_FILE)
    ts = TaggedCurve(123, metadata=None, session=mock_session)

    # act & assert
    with pytest.raises(CurveException):
        _ = ts.get_data_range()


@pytest.mark.parametrize("empty_status_code", [HTTPStatus.NO_CONTENT, HTTPStatus.NOT_FOUND])
def test_tagged_curve_get_data_range__empty(empty_status_code):
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(empty_status_code, None, None), config_file=CONFIG_FILE)
    ts = TaggedCurve(123, metadata=None, session=mock_session)

    # act & assert
    assert ts.get_data_range(date_to="1024-05-08") is None


@pytest.mark.parametrize("range_begin,range_end", [("2024-05-08T00:00:00+02:00", "2024-05-11T22:00:00+02:00"), (None, None)])
def test_tagged_instance_curve_get_data_range(range_begin, range_end):
    # arrange
    curve_id = 1234
    tag = "tag-123"
    param_from = "2024-05-03" 
    param_to = "2024-05-12"
    output_time_zone = "JST"
    issue_date = "2024-04-01"

    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.OK, range_begin, range_end), config_file=CONFIG_FILE)
    ts = TaggedInstanceCurve(curve_id, metadata=None, session=mock_session)

    # act
    range = ts.get_data_range(issue_date, tag, param_from, param_to, output_time_zone)

    # assert
    tz = ZoneInfo("Asia/Tokyo")
    assert mock_session.call_args == ["GET", "rtsp://test.host", f"/api/instances/tagged/{curve_id}/range?issue_date={issue_date}&tag={tag}&from={param_from}&to={param_to}"]
    assert range.begin == Range.parse_datetime(range_begin, tz)
    assert range.end == Range.parse_datetime(range_end, tz)


def test_tagged_instance_curve_get_data_range__exception():
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.INTERNAL_SERVER_ERROR, None, None), config_file=CONFIG_FILE)
    ts = TaggedInstanceCurve(123, metadata=None, session=mock_session)

    # act & assert
    with pytest.raises(CurveException):
        _ = ts.get_data_range("2024-05-08")


@pytest.mark.parametrize("empty_status_code", [HTTPStatus.NO_CONTENT, HTTPStatus.NOT_FOUND])
def test_tagged_instance_curve_get_data_range__empty(empty_status_code):
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(empty_status_code, None, None), config_file=CONFIG_FILE)
    ts = TaggedInstanceCurve(123, metadata=None, session=mock_session)

    # act & assert
    assert ts.get_data_range("2024-05-08", date_to="1024-05-08") is None


@pytest.mark.parametrize("range_begin,range_end", [("2024-05-08T00:00:00+02:00", "2024-05-11T22:00:00+02:00"), (None, None)])
def test_timeseries_curve_get_data_range(range_begin, range_end):
    # arrange
    curve_id = 1234
    param_from = "2024-05-03" 
    param_to = "2024-05-12"
    output_time_zone = "JST"
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.OK, range_begin, range_end), config_file=CONFIG_FILE)
    ts = TimeSeriesCurve(curve_id, metadata=None, session=mock_session)

    # act
    range = ts.get_data_range(param_from, param_to, output_time_zone)

    # assert
    tz = ZoneInfo("Asia/Tokyo")
    assert mock_session.call_args == ["GET", "rtsp://test.host", f"/api/series/{curve_id}/range?from={param_from}&to={param_to}"]
    assert range.begin == Range.parse_datetime(range_begin, tz)
    assert range.end == Range.parse_datetime(range_end, tz)


def test_timeseries_curve_get_data_range__exception():
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(HTTPStatus.INTERNAL_SERVER_ERROR, None, None), config_file=CONFIG_FILE)
    ts = TimeSeriesCurve(123, metadata=None, session=mock_session)

    # act & assert
    with pytest.raises(CurveException):
        _ = ts.get_data_range()


@pytest.mark.parametrize("empty_status_code", [HTTPStatus.NO_CONTENT, HTTPStatus.NOT_FOUND])
def test_timeseries_curve_get_data_range__empty(empty_status_code):
    # arrange
    mock_session = SessionMock(resp=RangeResponseMock(empty_status_code, None, None), config_file=CONFIG_FILE)
    ts = TimeSeriesCurve(123, metadata=None, session=mock_session)

    # act & assert
    assert ts.get_data_range(date_to="1024-05-08") is None