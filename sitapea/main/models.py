import datetime
from itertools import chain

from django.db import models
from django.db.models.functions import Coalesce
from django.utils import timezone

from main.helpers import (minutes_to_hhmm, Range, morning_shift, evening_shift,
                          get_each_day_in_range, get_overlap_of_ranges)

WORKDAY_MAX_DURATION = datetime.timedelta(minutes=26*60)


class Department(models.Model):
    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'

    name = models.CharField('Название', max_length=100)
    acronym = models.CharField('Сокращенно', max_length=20)

    def __str__(self):
        return self.name


class Employee(models.Model):
    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

    surname = models.CharField('Фамилия', max_length=50)
    name = models.CharField('Имя', max_length=50)
    patronym = models.CharField('Отчество', max_length=50, null=True, blank=True)
    code = models.CharField('Код сотрудника', max_length=20, unique=True)
    department = models.ForeignKey(Department)

    def __str__(self):
        return '{} {} {}'.format(self.surname, self.name, self.patronym)

    def get_last_checkin(self):
        last_checkin = self.checkin_set\
            .annotate(arrival_or_leaving=Coalesce('arrival_timestamp', 'leaving_timestamp'))\
            .order_by('-arrival_or_leaving')[:1]
        if last_checkin:
            return last_checkin[0]

    def arrive(self):
        leaving = self.get_last_checkin()
        self.checkin_set.create(arrival_timestamp=timezone.now())
        if not leaving.leaving_timestamp:
            raise ValueError('forgot_to_leave')

    def leave(self):
        arrival = self.get_last_checkin()
        if not arrival.leaving_timestamp and \
                ((arrival.arrival_timestamp - timezone.now()) < WORKDAY_MAX_DURATION):
            arrival.leaving_timestamp = timezone.now()
            arrival.save()
        else:
            self.checkin_set.create(leaving_timestamp=timezone.now())
            raise ValueError('forgot_to_leave_and_arrive')
        if not arrival.arrival_timestamp:
            raise ValueError('forgot_to_arrive')

    def working_hours_summary_in_date_range(self, date_from, date_to):
        checkin_set = self.checkin_set\
            .annotate(arrival_or_leaving=Coalesce('arrival_timestamp', 'leaving_timestamp'))\
            .filter(arrival_timestamp__date__gte=date_from)\
            .filter(leaving_timestamp__date__lt=date_to)
        last_nights_checkin_set = self.checkin_set \
            .annotate(arrival_or_leaving=Coalesce('arrival_timestamp', 'leaving_timestamp')) \
            .filter(arrival_timestamp__date__lt=date_to)\
            .filter(leaving_timestamp__date__gte=date_to)
        checkin_set = list(chain(checkin_set, last_nights_checkin_set))
        result = 0
        for checkin in checkin_set:
            result += checkin.workday_duration if checkin.workday_duration else 0
        result = minutes_to_hhmm(result)
        return result

    def working_hours_wo_night_shift_in_date_range(self, date_from, date_to):
        checkin_set = self.checkin_set\
            .annotate(arrival_or_leaving=Coalesce('arrival_timestamp', 'leaving_timestamp'))\
            .filter(arrival_timestamp__date__gte=date_from)\
            .filter(leaving_timestamp__date__lt=date_to)
        last_nights_checkin_set = self.checkin_set \
            .annotate(arrival_or_leaving=Coalesce('arrival_timestamp', 'leaving_timestamp')) \
            .filter(arrival_timestamp__date__lt=date_to)\
            .filter(leaving_timestamp__date__gte=date_to)
        checkin_set = list(chain(checkin_set, last_nights_checkin_set))
        result = 0
        for checkin in checkin_set:
            result += checkin.workday_wo_night_shift_bonus if checkin.workday_wo_night_shift_bonus else 0
        result = minutes_to_hhmm(result)
        return result


class CheckIn(models.Model):
    class Meta:
        verbose_name = 'Отметка'
        verbose_name_plural = 'Отметки'

    employee = models.ForeignKey(Employee)
    arrival_timestamp = models.DateTimeField('Время прибытия', null=True, blank=True)
    leaving_timestamp = models.DateTimeField('Время ухода', null=True, blank=True)
    comment = models.TextField('Комментарий', null=True, blank=True)

    def __str__(self):
        return '{} ({} - {})'.format(
            self.employee, self.arrival_timestamp, self.leaving_timestamp
        )

    @property
    def working_time_range(self):
        return Range(start=timezone.localtime(self.arrival_timestamp),
                     end=timezone.localtime(self.leaving_timestamp))

    @property
    def workday_duration_raw(self):
        if self.leaving_timestamp and self.arrival_timestamp:
            arrival_timestamp = timezone.localtime(self.arrival_timestamp)
            leaving_timestamp = timezone.localtime(self.leaving_timestamp)
            if leaving_timestamp.date() == arrival_timestamp.date():
                worktime_timedelta = leaving_timestamp - arrival_timestamp
                coef = 1.5 if arrival_timestamp.weekday() >= 5 else 1
                return int(worktime_timedelta.total_seconds() // 60 * coef)
            else:
                total = 0
                next_date = arrival_timestamp.date()
                next_timestamp = timezone.make_aware(datetime.datetime(year=next_date.year, month=next_date.month, day=next_date.day))
                next_timestamp += datetime.timedelta(days=1)
                coef = 1.5 if arrival_timestamp.weekday() >= 5 else 1
                total += (next_timestamp - arrival_timestamp).total_seconds() // 60 * coef
                start_date = leaving_timestamp.date()
                start_timestamp = timezone.make_aware(datetime.datetime(year=start_date.year, month=start_date.month, day=start_date.day))
                coef = 1.5 if leaving_timestamp.weekday() >= 5 else 1
                total += (leaving_timestamp - start_timestamp).total_seconds() // 60 * coef
                i = arrival_timestamp.date() + datetime.timedelta(days=1)
                while i < leaving_timestamp.date():
                    coef = 1.5 if i.weekday() >= 5 else 1
                    total += 1440 * coef
                    i += datetime.timedelta(days=1)
                return int(total)

    @property
    def dinners_duration(self):
        raw = self.workday_duration_raw
        if raw:
            dinners_count = (raw + 7*60) // 12 // 60
            return dinners_count * 60

    @property
    def coffee_duration(self):
        raw = self.workday_duration_raw
        if raw:
            div = raw // (12*60) * 7*60
            mod = max(raw % (12*60) - 5*60, 0)
            coffee_breaks_count = (div + mod) // 135
            return coffee_breaks_count * 15

    @property
    def night_shift_minutes(self):
        result = 0
        if self.workday_duration_raw and self.arrival_timestamp > timezone.make_aware(datetime.datetime(2017, 1, 1)):
            for day in get_each_day_in_range(self.working_time_range):
                assert day.start.day == day.end.day
                result += get_overlap_of_ranges(day, morning_shift(day.start.date()))
                result += get_overlap_of_ranges(day, evening_shift(day.start.date()))
        return result

    @property
    def night_shift_bonus(self):
        return int(self.night_shift_minutes * 0.5)

    @property
    def workday_duration(self):
        raw = self.workday_duration_raw
        if raw:
            return raw - self.dinners_duration - self.coffee_duration + self.night_shift_bonus
        return 0

    @property
    def workday_wo_night_shift_bonus(self):
        raw = self.workday_duration_raw
        if raw:
            return raw - self.dinners_duration - self.coffee_duration
        return 0

    @property
    def workday_duration_in_hhmm(self):
        if self.workday_duration:
            return minutes_to_hhmm(self.workday_duration)
