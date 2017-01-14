from django.db.models.functions import Coalesce
from django.utils.timezone import localtime
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView, View
from openpyxl import Workbook
from main.models import Employee, CheckIn


class IndexView(TemplateView):
    template_name = 'main/index.html'


class CheckInView(View):
    def post(self, request, code, action):
        if request.is_ajax:
            try:
                employee = Employee.objects.get(code=code)
                json_response = {
                    'employee_name': employee.name,
                    'employee_surname': employee.surname,
                    'action': action,
                }
                try:
                    if action == 'arrival':
                        employee.arrive()
                    elif action == 'leaving':
                        employee.leave()
                except ValueError as e:
                    json_response['warning'] = str(e)
                finally:
                    return JsonResponse(json_response)
            except Employee.DoesNotExist:
                return JsonResponse({'error': 'employee_does_not_exist'})


class ReportDownloadView(View):
    def get(self, request, date_from, date_to=None):

        wb = Workbook()
        ws = wb.active

        ws.append(('Отчёт за период', date_from, date_to))
        titles = (
            'Фамилия',  # A
            'Имя',  # B
            'Отчество',  # C
            'Отдел',  # D
            'Приход',  # E
            'Уход',  # F
            'Отработано минут',  # G
            'Отработано часов:минут',  # H
            'Комментарий',  # I
            'Обеды',  # J
            'Перерывы',  # K
            'Бонус за ночную смену',  # L
            'Чистая разница',  # M
        )
        ws.append(titles)
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 20
        ws.column_dimensions['E'].width = 20
        ws.column_dimensions['F'].width = 20
        ws.column_dimensions['I'].width = 60
        ws.column_dimensions.group('J', 'M', hidden=True)
        qs = CheckIn.objects\
            .annotate(arrival_or_leaving=Coalesce('arrival_timestamp', 'leaving_timestamp'))\
            .order_by('employee__surname', 'employee__name', 'arrival_or_leaving')\
            .select_related('employee', 'employee__department')
        if date_to:
            qs = qs.filter(arrival_or_leaving__date__gte=date_from)
            qs = qs.filter(arrival_or_leaving__date__lt=date_to)
        else:
            qs = qs.filter(arrival_or_leaving__date=date_from)

        for checkin in qs:
            row = (
                checkin.employee.surname,
                checkin.employee.name,
                checkin.employee.patronym,
                checkin.employee.department.acronym,
                localtime(checkin.arrival_timestamp).replace(tzinfo=None) if checkin.arrival_timestamp else None,
                localtime(checkin.leaving_timestamp).replace(tzinfo=None) if checkin.leaving_timestamp else None,
                checkin.workday_duration,
                checkin.workday_duration_in_hhmm,
                checkin.comment,
                checkin.dinners_duration,
                checkin.coffee_duration,
                checkin.night_shift_bonus,
                checkin.workday_duration_raw,
            )
            ws.append(row)

        response = HttpResponse(content_type="application/ms-excel")
        filename = 'sitapea_report_{}{}.xlsx'.format(date_from, '_'+date_to if date_to else '')
        response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
        wb.save(response)
        return response


class SummaryReportView(View):
    def get(self, request, date_from, date_to):

        wb = Workbook()
        ws = wb.active

        ws.append(('Суммарный отчёт за период', date_from, date_to))
        titles = (
            'Фамилия',
            'Имя',
            'Отчество',
            'Отдел',
            'Отработано часов:минут',
        )
        ws.append(titles)
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 20
        qs = Employee.objects\
            .order_by('surname', 'name')\
            .select_related('department')

        for employee in qs:
            working_hours_summary = employee.working_hours_summary_in_date_range(date_from, date_to)
            row = (
                employee.surname,
                employee.name,
                employee.patronym,
                employee.department.acronym,
                working_hours_summary,
            )
            ws.append(row)

        response = HttpResponse(content_type="application/ms-excel")
        filename = 'sitapea_summary_report_{}{}.xlsx'.format(date_from, '_'+date_to if date_to else '')
        response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
        wb.save(response)
        return response

