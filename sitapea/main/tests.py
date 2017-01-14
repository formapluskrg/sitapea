from datetime import datetime as dt

from django.test import TestCase
from django.utils.timezone import make_aware

from .models import CheckIn


class TestNightShifts(TestCase):
    def test_night_shift_1(self):
        checkin = CheckIn(
            arrival_timestamp=make_aware(dt(2017, 1, 1, 10, 0)),
            leaving_timestamp=make_aware(dt(2017, 1, 1, 23, 0))
        )
        self.assertEqual(checkin.night_shift_minutes, 60)

    def test_night_shift_2(self):
        checkin = CheckIn(
            arrival_timestamp=make_aware(dt(2017, 1, 1, 4, 0)),
            leaving_timestamp=make_aware(dt(2017, 1, 1, 14, 0))
        )
        self.assertEqual(checkin.night_shift_minutes, 120)

    def test_night_shift_3(self):
        checkin = CheckIn(
            arrival_timestamp=make_aware(dt(2017, 1, 1, 3, 0)),
            leaving_timestamp=make_aware(dt(2017, 1, 1, 23, 0))
        )
        self.assertEqual(checkin.night_shift_minutes, 240)

    def test_night_shift_4(self):
        checkin = CheckIn(
            arrival_timestamp=make_aware(dt(2017, 1, 1, 23, 0)),
            leaving_timestamp=make_aware(dt(2017, 1, 2, 4, 0))
        )
        self.assertEqual(checkin.night_shift_minutes, 300)

    def test_night_shift_5(self):
        checkin = CheckIn(
            arrival_timestamp=make_aware(dt(2017, 1, 1, 20, 0)),
            leaving_timestamp=make_aware(dt(2017, 1, 2, 4, 0))
        )
        self.assertEqual(checkin.night_shift_minutes, 360)

    def test_night_shift_6(self):
        checkin = CheckIn(
            arrival_timestamp=make_aware(dt(2017, 1, 1, 2, 0)),
            leaving_timestamp=make_aware(dt(2017, 1, 2, 10, 0))
        )
        self.assertEqual(checkin.night_shift_minutes, 720)
