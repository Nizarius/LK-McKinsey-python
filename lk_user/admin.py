# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from lk_user.models import LkUser
from django.contrib.auth.admin import UserAdmin #to protect password
from project.models import Team, Skill

class LkUserAdmin(UserAdmin):
    add_form_template = 'admin/auth/user/add_form.html'
    change_user_password_template = None
    fieldsets = (
        (None, {'fields': ('email', 'password', 'is_admin', 'name', 'sername', 'phone_number', 'skills', 'want_join', 'team', )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email','is_admin', 'name', 'password1', 'password2', 'skills', 'want_join', 'team', ),
        }),
    )
    list_display = (
        'email',
        'name',
        'sername',
        'is_admin',
        'team',
    )
    list_filter = ()
    search_fields = ('email','name', 'sername', )
    filter_horizontal = ('skills', 'want_join',)
    ordering = ()
    inlines = [ ]


admin.site.register(LkUser, LkUserAdmin)
