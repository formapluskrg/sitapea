"""sitapea URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from main.views import CheckInView, IndexView, ReportDownloadView

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^checkin/(?P<code>\d*)/(?P<action>arrival|leaving)/$', CheckInView.as_view(), name='checkin-view'),
    url(r'^report/(?P<date_from>([0-9]{4})-(0[1-9]|1[0-2])-([1-9]|0[1-9]|[1-2][0-9]|3[0-1])).*'
        r'/(?P<date_to>([0-9]{4})-(0[1-9]|1[0-2])-([1-9]|0[1-9]|[1-2][0-9]|3[0-1])).*/$',
        ReportDownloadView.as_view(), name='report-range-download-view'),
    url(r'^$', IndexView.as_view(), name='index-view'),
]
