from django.conf.urls import url
from lk_user import views

urlpatterns = [
    url(r'^register/?$', views.register),
    url(r'^login/?$', views.login),
    url(r'^logout/?$', views.logout),
    url(r'^confirm/?$', views.confirm),
    url(r'^send_drop_letter/?$', views.send_drop_letter),
    url(r'^drop/?$', views.drop_password_page),
    url(r'^drop_password/?$', views.drop_password),
    url(r'^profile/edit/?$', views.edit_user),
    url(r'^profile/edit_skills/?$', views.edit_skills),
    url(r'^profile/edit_avatar/?$', views.edit_avatar),
    url(r'^profile/del_experience/?$', views.del_experience),
    url(r'^profile/edit_experience/?$', views.edit_experience),
    url(r'^profile/invite/?$', views.invite_user),
    url(r'^profile/?$', views.my_profile),
    url(r'^search/?$', views.search_users),
    url(r'^auth/?$', views.auth_page),
    url(r'^(\d{1,10})/?$', views.profile),
    url(r'^$', views.participants),
    # url(r'', include('project.urls')),
]
