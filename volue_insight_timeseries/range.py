from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict

import pandas as pd
from volue_insight_timeseries.util import parse_tz


@dataclass
class Range:
    """A range is defined by two points in time (begin and end).

    Begin and end are datetime respresented with ZoneInfo objects. 
    Begin is inclusive, end is exclusive.
    """
    begin: Optional[datetime] = None
    end: Optional[datetime] = None

    @classmethod
    def from_dict(cls, range_dict: Dict, tz_name: str = ''):
        if not tz_name:
            tz_name = 'CET'

        # wapi server returns {"empty": True} for empty Range
        if range_dict.get('empty'):
            return cls()

        tz = parse_tz(tz_name)
        begin = end = None
        if range_dict:
            begin = cls.parse_datetime(range_dict.get('begin'), tz)
            end = cls.parse_datetime(range_dict.get('end'), tz)
        return cls(begin, end)

    @classmethod
    def parse_datetime(cls, s: Optional[str], tz: datetime.tzinfo) -> Optional[datetime]:
        # “Z” is replaced by “+00:00" because it is not handled by the datetime library
        return datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(tz) if s else None

    def is_finite(self):
        return self.begin and self.end

    def to_pandas(self):
        if not self.is_finite():
            raise ValueError('Range must be finite to convert it to pd.Interval.')

        left = pd.Timestamp(self.begin)
        right = pd.Timestamp(self.end)
        return pd.Interval(left, right, closed='left')
