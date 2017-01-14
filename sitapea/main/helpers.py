from datetime import datetime as dt, time
from collections import namedtuple

from django.utils.timezone import make_aware

Range = namedtuple('Range', ['start', 'end'])


def minutes_to_hhmm(minutes_total):
    hours = minutes_total // 60
    minutes = minutes_total % 60
    return "%d:%02d" % (hours, minutes)


def morning_shift(date):
    return Range(
        start=make_aware(dt.combine(date, time.min)),
        end=make_aware(dt.combine(date, time(6)))
    )


def evening_shift(date):
    return Range(
        start=make_aware(dt.combine(date, time(22))),
        end=make_aware(dt.combine(date, time.max))
    )


def get_each_day_in_range(datetime_range):
    if datetime_range.start.day == datetime_range.end.day:
        return [datetime_range]
    else:
        return [
            Range(start=datetime_range.start,
                  end=make_aware(dt.combine(datetime_range.start.date(), time.max))),
            Range(start=make_aware(dt.combine(datetime_range.end.date(), time.min)),
                  end=datetime_range.end),
        ]


def get_overlap_of_ranges(r1, r2):
    latest_start = max(r1.start, r2.start)
    earliest_end = min(r1.end, r2.end)
    return round((earliest_end - latest_start).seconds / 60) if earliest_end > latest_start else 0
