from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='arms_index'),
    url(r'^session/add/$', views.add_session, name='add_session'),
    url(r'^session/(?P<session_id>[0-9]+)/addfiles/$', views.add_data, name='add_data'),
    url(r'^session/(?P<session_id>[0-9]+)/savefiles/$', views.save_session, name='save_session'),
    url(r'^session/(?P<session_id>[0-9]+)/remove/datafile/(?P<file_id>[0-9]+)/$', views.remove_datafile, name='remove_datafile'),
    url(r'^session/(?P<session_id>[0-9]+)/remove/$', views.remove_session, name='remove_session'),
    url(r'^session/(?P<session_id>[0-9]+)/viewdata/$', views.view_data, name='view_data'),
    url(r'^session/dashboard/$', views.dashboard, name='dashboard'),
]