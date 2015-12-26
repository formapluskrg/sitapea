from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db.models.functions import Coalesce
from django.utils.safestring import mark_safe
from .models import Employee, Department, CheckIn


class EmployeeInline(admin.TabularInline):
    model = Employee
    extra = 1


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'acronym', )
    inlines = [
        EmployeeInline,
    ]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('surname', 'name', 'patronym', 'code', )


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ('employee', 'department',
                    'arrival_timestamp_with_custom_sort', 'leaving_timestamp',
                    'workday_duration_raw', 'dinners_duration', 'coffee_duration', 'workday_duration',
                    'comment', )
    list_filter = ('employee__surname', )

    def get_queryset(self, request):
        qs = super(CheckInAdmin, self).get_queryset(request)
        qs = qs.annotate(arrival_or_leaving=Coalesce('arrival_timestamp', 'leaving_timestamp'))\
            .order_by('-arrival_or_leaving')
        return qs

    def department(self, obj):
        return obj.employee.department.acronym
    department.short_description = 'Отдел'

    def arrival_timestamp_with_custom_sort(self, obj):
        return obj.arrival_timestamp
    arrival_timestamp_with_custom_sort.admin_order_field = 'arrival_or_leaving'
    arrival_timestamp_with_custom_sort.short_description = 'Время прибытия'

    def report_link(self, obj):
        if obj.arrival_timestamp:
            date = obj.arrival_timestamp.strftime('%Y-%m-%d')
            return mark_safe('<a href="{}">{}</a>'.format(
                    reverse('report-download-view', kwargs={'date_from': date}),
                    date,
            ))
    report_link.short_description = 'Скачать отчёт'
