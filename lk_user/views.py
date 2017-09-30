# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from lk_user.models import LkUser
from project.models import Team, Experience, Skill, SkillGroup
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.db.models import Q, Prefetch
from django.core import serializers
from django.core.mail import send_mail
from mckinslk.settings import BASE_DIR

import logging
import json
import sys 
import os

reload(sys)
sys.setdefaultencoding('utf-8')
logger = logging.getLogger('django')

#TODO:
# отсортить выдачу по скилам в поиске участников
# оптимизировать поиск

def build_skills():
    skill_groups = SkillGroup.objects.all()
    for skill_group in skill_groups:
        skill_group.skills = Skill.objects.filter(group = skill_group)
    return skill_groups
    
@login_required(login_url='/participants/auth')
def profile(request, user_id):
    user_id = int(user_id)
    logger.info(user_id)
    if request.method == 'GET':
        params = {}
        
        if request.user.is_authenticated:
            params['user'] = request.user
            
        try:
            params['profile_user'] = LkUser.objects.filter(id = user_id).prefetch_related(Prefetch('skills', to_attr='user_skills'))[0]
            if params['profile_user'].is_hidden and not request.user.team is None and request.user.team.id != params['profile_user'].team.id:
                raise Http404("Пользователя не существует")
            else:
                params['skill_groups'] = build_skills()
                params['experience'] = Experience.objects.filter(owner = params['profile_user'])
                
                params['profile_user'].accept = False
                params['profile_user'].join = False
                if request.user.is_authenticated and request.user.team and params['profile_user'] in request.user.team.want_accept.all():
                    params['profile_user'].accept = True
                    
                if request.user.is_authenticated and request.user.team in params['profile_user'].want_join.all():
                    params['profile_user'].join = True
                
                if request.GET.get('popup', None):
                    return render(request, 'ajax/user_page.html', params)  
                else:
                    return render(request, 'participants/user_profile.html', params)  
                    
        except Exception,e:
            logger.warning(e)
            raise Http404("Пользователя не существует")


@login_required(login_url='/participants/auth')
def my_profile(request):
    if request.method == 'GET':
        params = {}
        if request.user.is_authenticated():
            params['user'] = LkUser.objects.filter(id = request.user.id).prefetch_related(Prefetch('skills', to_attr='user_skills')).prefetch_related(Prefetch('want_join', to_attr='join'))[0]
            params['skill_groups'] = build_skills()
            params['experience'] = Experience.objects.filter(owner = params['user'])
            params['accept'] = Team.objects.filter(want_accept__id = params['user'].id)
            return render(request, 'participants/cabinet.html', params) 

                
@login_required(login_url='/participants/auth')    
def participants(request):
    if request.method == 'GET':
        params = {}
        
        if request.user.is_authenticated:
            params['user'] = request.user
        params['skill_groups'] = build_skills()
        return render(request, 'participants/participants.html', params)      
        

def auth_page(request):
    if request.method == 'GET':
        params = {}
        
        if request.user.is_authenticated:
            if params.get('next'):
                return HttpResponseRedirect(params['next'])
            return HttpResponseRedirect('/participants/profile')
            
        return render(request, 'participants/authorization.html', params) 
        
        
def confirm_user(request):
    if request.method == 'GET':        
        confirm = request.GET.get('c')
        
        if request.user.is_authenticated():
            auth.logout(request)
        
        try:
            user = LkUser.objects.get(password = confirm)
            user.is_active = True
            user.save()
        except Exception, e:
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Пользователя несуществует'}), content_type='application/json')

        return HttpResponse(json.dumps({'status': 'ok', 'redirect': 'participants/auth'}), content_type='application/json')


def send_email(request):
    if request.method == 'POST':        
        params = request.POST
        
        if not (params.get('message') and (params.get('user') or params.get('team'))):
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Введены неверные данные'}), content_type='application/json')
            
        if not request.user.is_authenticated():
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Войдите в свою учетную запись', 'redirect': '/participants/auth'}), content_type='application/json')
        
        if request.user.is_hidden or not request.user.is_active:
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Ваш аккаунт скрыт для общения. Пожалуйста откройте публичный доступ к вашему аккаунту, если хотите написать пользователю.', 'redirect': '/participants/auth'}), content_type='application/json')
        
        if params.get('user'):
            try:
                user = LkUser.objects.get(id = params['user'])
            except Exception, e:
                return HttpResponse(json.dumps({'status': 'error', 'message': 'Пользователя не существует'}), content_type='application/json')
        elif params.get('team'):
            try:
                team = Team.objects.get(id = params['team'])
                user = LkUser.objects.get(id = team.creater_id)
            except Exception, e:
                return HttpResponse(json.dumps({'status': 'error', 'message': 'Пользователя или команды не существует'}), content_type='application/json')
            
        message = params['message'].replace('\n', '<br>')
        
        send_mail(
            'Новое сообщение', 
            '',
            'info@bigdata-hack.ru', 
            [user.email], 
            fail_silently=False, 
            html_message = '''
            Здравствуйте, {}! <br>
            У вас новое сообщение от <a href="http://bigdata-hack.ru/participants/{}/">{}</a><br><br><br>
            {}
            <br><br><br>
            C Уважением, администрация bigdata-hack :)'''.format(user.name,  request.user.id, request.user.name, message), 
        )
        

        return HttpResponse(json.dumps({'status': 'ok', 'redirect': 'participants/auth'}), content_type='application/json')


def drop_password_page(request):
    if request.method == 'GET':        
        confirm = request.GET.get('c')
        
        if request.user.is_authenticated():
            auth.logout(request)
        
        return render(request, 'participants/drop_password.html', { 'c': confirm }) 

def drop_password(request):
    if request.method == 'POST':        
        params = request.POST
        
        if params.get('password') and params.get('password_confirm') and params.get('c'):
            if params['password'] != params['password_confirm']:
                return HttpResponse(json.dumps({'status': 'error', 'message': 'Пароли не совпадают'}), content_type='application/json')
            
            try:
                user = LkUser.objects.get(password = params['c'])
                user.set_password(params['password'])
                user.save()
            except Exception, e:
                return HttpResponse(json.dumps({'status': 'error', 'message': 'Пользователя несуществует'}), content_type='application/json')
        else:
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Не введены все данные'}), content_type='application/json')
        

        return HttpResponse(json.dumps({'status': 'ok', 'redirect': '/participants/auth'}), content_type='application/json')

def send_confirm_email(request):
    send_mail(
        'Подтверждение электронной почты', 
        '<a href="moscow/user"> Сюда </a>', 
        'info@bigdata-hack.ru', 
        ['ddenis1@yandex.ru'], 
        fail_silently=False, 
    )    
    logger.info("was Send")
    return HttpResponse(json.dumps({'status': 'ok' }), content_type='application/json')


def send_drop_letter(request):
    if request.method == 'GET':  
        params = request.GET
        
        if params.get('email'):
            email = params['email']
            try:
                user = LkUser.objects.get(email = email)
            except Exception, e:
                return HttpResponse(json.dumps({'status': 'error', 'message': 'Пользователя с таким email не сущетсвует'}), content_type='application/json')
                
        else:
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Введите имейл'}), content_type='application/json')
        
        send_mail(
            'Сброс пароля', 
            '',
            'info@bigdata-hack.ru', 
            [email], 
            fail_silently=False, 
            html_message = '''
            Здравствуйте, {}!<br><br>
            Вы отправили заявку на сброс пароля на bigdata-hack.ru<br>
            Для сброса пароля перейдите по ссылке<br>
            <a href="http://bigdata-hack.ru/participants/drop_page/?c={}">http://bigdata-hack.ru/participants/drop_page/?c={}</a>
            <br>Если это были не вы - проигнорируйте это письмо 
            <br><br>C Уважением, администрация bigdata-hack :)'''.format(user.name, user.password, user.password), 
        ) 
        
        return HttpResponse(json.dumps({'status': 'ok', 'message': 'На ваш почтовый ящик было отправленно письмо с дальнейшими инструкциями по восстановлению доступа'}), content_type='application/json')


def register(request):
    if request.method == 'POST':
        reg_info = request.POST
        logger.info(reg_info)
        if reg_info.get('email') is None or reg_info.get('password') is None or reg_info.get('phone_number') is None or reg_info.get('name') is None or reg_info.get('password_confirm') is None:
            result = {'status': 'error', 'message': 'Не введены все данные'}
            logger.error('No enough data for create account')
            return HttpResponse(json.dumps(result), content_type='application/json')

        if str(reg_info['password']) == str(reg_info['password_confirm']):
            if LkUser.objects.filter(email = reg_info['email']):
                result = {'status': 'error', 'message': 'Пользователь с таким email уже существует'}
                logger.error('Duplicate email' + reg_info['email'])
            else:
                new_user = LkUser.objects.create_user(
                    reg_info['email'], reg_info['password'], reg_info['password_confirm']
                ) 
                new_user.name = str(reg_info['name']) 
                new_user.phone_number = str(reg_info['phone_number'])
                new_user.set_password(reg_info['password'])
                new_user.is_active = False
                new_user.save()
                
                send_mail(
                    'Подтверждение регистрации', 
                    '',
                    'info@bigdata-hack.ru', 
                    [new_user.email], 
                    fail_silently=False, 
                    html_message = '''
                    Здравствуйте, {}!<br><br>
                    Поздравляем вас с регистрации на bigdata-hack.ru!<br><br>
                    Логин: {}<br>
                    Пароль: {}<br>
                    Для подтверждения электронной почты перейдите по ссылке<br>
                    <a href="http://bigdata-hack.ru/participants/confirm/?c={}">http://bigdata-hack.ru/participants/confirm/?c={}</a><br><br>
                    C Уважением, администрация bigdata-hack :)'''.format(new_user.name, new_user.email, reg_info['password'], new_user.password, new_user.password), 
                ) 
                
                #TODO: confirm email
                logger.info('User ' + new_user.email + ' created successfully')
                result = {'status': 'ok', 'redirect': '/participants/profile'}
        else:
            result = {'status': 'error', 'message': 'Пароли не совпадают'}
            logger.error('Wrong password checking')
        
        return HttpResponse(json.dumps(result), content_type='application/json')

    
def login(request):
    if request.method == 'POST': #POST
        login_info = request.POST
        if not (login_info.get('email') and login_info.get('password')):
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Неправильные данные для авторизации'}), content_type='application/json' ,)
        
        if request.user.is_authenticated():
            auth.logout(request)
                
        user = auth.authenticate(email = login_info['email'], password = login_info['password'])
        result = {}
        if user is None:
            result = {'status': 'error', 'message': 'Пользователь не найден или были введены неверные данные'}
        elif not user.is_active:
            result = {'status': 'error', 'message': 'Пользователь не подтвержден'}
        else:
            auth.login(request, user)
            return HttpResponse(json.dumps({ 'status' : 'ok', 'redirect' : '/participants/profile' }), content_type='application/json')
        
        return HttpResponse(json.dumps(result), content_type='application/json')


def logout(request):
    if request.method == 'POST':
        if request.user.is_authenticated():
            auth.logout(request)
        return HttpResponseRedirect('/')


def confirm(request):
    if request.method == 'GET':
        params = request.GET
        confirm = params.get('c')
        try:
            user = LkUser.objects.get(password = confirm)
            user.is_active = True
            user.save()
            return HttpResponseRedirect('/participants/auth')
        except Exception, e:
            raise Http404("Пользователя не существует")


def edit_user(request):
    if request.method == 'POST': #POST
        update_info = request.POST
        
        if not request.user.is_authenticated(): 
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Войдите в свою учетную запись'}), content_type='application/json')  
        
        user = request.user
        if update_info.get('password'):
            user.set_password(update_info['password'])  
        if update_info.get('phone_number'):
            user.phone_number = update_info['phone_number']  
        if update_info.get('name'):
            user.name = update_info['name']  
        if update_info.get('is_hidden'):
            if update_info['is_hidden'] == 'true':
                user.is_hidden = True 
            elif update_info['is_hidden'] == 'false':    
                user.is_hidden = False 
        
        user.save()
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json')  
 

def del_experience(request):
    if request.method == 'POST': #POST
        params = request.POST
        
        if not request.user.is_authenticated(): 
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Войдите в свою учетную запись'}), content_type='application/json')  
        
        if not params.get('id'):
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Нет указателя на удаляемый опыт'}), content_type='application/json')  
        try:
            experience = Experience.objects.get(id = params['id'])
            experience.delete()

            logger.error('Experience deleted ' + str(params['id']) + 'by user' + str(request.user.id))
            return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json')  
        except Exception,e:
            logger.error('Experience not found ' + str(params['id']) + 'by user' + str(request.user.id))
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Неверны идентификатор опыта'}), content_type='application/json')  
                


def edit_experience(request):
    if request.method == 'POST': #POST
        params = request.POST
        
        if not request.user.is_authenticated(): 
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Войдите в свою учетную запись'}), content_type='application/json')  
        
        if not params.get('text'):
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Пустое текстовое поле'}), content_type='application/json')  

        if params.get('id'):
            try:
                experience = Experience.objects.get(id = params['id'])
                experience.text = params['text']
                experience.save()
            except Exception,e: 
                logger.warning('Not found experience id' + str(params['id']))
                Experience.objects.create(text = params['text'], owner = request.user)
        else:
            experience = Experience.objects.create(text = params['text'], owner = request.user)
            logger.info('Experience created' + str(experience.id))
            
            
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json')  


def edit_skills(request):
    if request.method == 'POST': #POST
        params = request.POST
        
        if not request.user.is_authenticated(): 
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Войдите в свою учетную запись'}), content_type='application/json')  
        
        if not params.get('ids'):
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Пустое текстовое поле'}), content_type='application/json')  

        skill_ids = json.loads(params['ids'])
        if len(skill_ids) == 0 or len(skill_ids) > 3:
            result = {'status': 'error', 'message': 'Непредвиденная ошибка'}
        skills = Skill.objects.filter(id__in = skill_ids).distinct()
        
        request.user.skills.clear()
        request.user.skills.add(*skills)
        request.user.save()
        return HttpResponse(json.dumps({ 'status': 'ok' }), content_type='application/json')
    

def search_users(request):
    if request.method == 'GET':
        params = request.GET
        

        query = (Q(team__isnull = True) | Q(team__member_count__lte = 1)) & Q(is_hidden=False)
        
        if request.user.is_authenticated:
            query = query & ~Q(id = request.user.id)
            
        if not request.user.team is None:
            query = query & ~Q(team = request.user.team)
        
        if params.get('name'):
            name = str(params['name']).lower().split()
            last_name = None
            
            if len(name) > 1:
                last_name = name[1]
            name = name[0]
            
            if last_name is None:
                query = query & Q(name__icontains = name) 
            else:
                query = query & (Q(name__icontains = params['name'].lower()) | Q(name__icontains = name) | Q(name__icontains = last_name))
                
            
        users = LkUser.objects.filter(query).prefetch_related(Prefetch('skills', to_attr='user_skills'))

        if params.get('skills'):
            skill_ids = json.loads(params['skills'])
            
            if len(skill_ids) == 0:
                return HttpResponse(json.dumps({'status': 'error', 'message': 'Непредвиденная ошибка'}), content_type='application/json')
            
            skills = set(Skill.objects.filter(id__in = skill_ids))
            users = filter(lambda u: set(u.user_skills) >= skills, users)
                
        
        if params.get('team_need', None) and params['team_need'] == 'true':
            
            if not request.user.is_authenticated:
                return HttpResponse(json.dumps({'status': 'error', 'message': 'Войдите в свою учетную запись'}), content_type='application/json')
            
            if request.user.team is None:
                return HttpResponse(json.dumps({'status': 'error', 'message': 'У вас нет команды'}), content_type='application/json')
            
            skills = request.user.team.need_skills.all()
            users = filter(lambda u: len(u.user_skills & skills) >= 1, users)
            
            
        if params.get('name'):
            for user in users:
                user.pos = user.get_search_name().find("".join(str(params['name']).lower().split()))
            users = sorted(users, key = lambda uu: uu.pos)

            
        offset = int(params.get('offset', 0))
        limit = int(params.get('limit', 20))
        users = users[offset : offset + limit]
        
        if request.user.is_authenticated() and not request.user.team is None:
            want_accept_set = set(request.user.team.want_accept.all())
            want_join_set = set(LkUser.objects.filter(want_join__id = request.user.team.id))
            for user in users:
                user.accept = False
                user.join = False
                if user in want_accept_set:
                    user.accept = True
                    
                if user in want_join_set:
                    user.join = True
                
        if params.get('want_html', None):
            return render(request, 'ajax/user.html', { 'users': users })
            
            
        return HttpResponse(json.dumps({'status': 'ok', 'users': serializers.serialize("json", users)}), content_type='application/json')


def invite_user(request):
    if request.method == 'POST': #POST
        params = request.POST
        if not request.user.is_authenticated:
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Войдите в свою учетную запись'}), content_type='application/json')
        
        team = request.user.team
        
        if team is None:
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Создайте команду'}), content_type='application/json')
        
        if team.creater_id != request.user.id:
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Приглашать в команду может только создатель'}), content_type='application/json')
            
        if team.member_count >= 5 or team.is_hidden:
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Команда заполнена или скрыта'}), content_type='application/json')
            
        if not params.get('id'):
            logger.error('No enough data to invite user')
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Нет данных'}), content_type='application/json')

        else:
            try:
                user = LkUser.objects.filter(id = params['id']).prefetch_related(Prefetch('want_join', to_attr='join'))[0]
            except Exception, e:
                logger.error(e)
                return HttpResponse(json.dumps({'status': 'error', 'message': 'Пользователь не найден'}), content_type='application/json')
            
            if team in user.join:
                if not user.is_hidden and (not user.team or user.team and user.team.member_count == 1):
                    team.want_accept.remove(user)    
                    team.member_count += 1
                    if team.member_count >= 5:
                        team.want_accept.clear()
                    
                    if user.team:
                        user.team.delete()
                    user.team = team
                    user.want_join.clear()
                    result = 'accepted'
                    user.save()
                    team.save()
                    
                    send_mail(
                        'Принятие в команду', 
                        '',
                        'info@bigdata-hack.ru', 
                        [user.email], 
                        fail_silently=False, 
                        html_message = '''
                        Здравствуйте, {}! <br><br>
                        Поздравляем! Вас приняли в команду <a href="http://bigdata-hack.ru/teams/{}">{}</a>.<br><br>
                        C Уважением, администрация bigdata-hack :)'''.format(user.name, team.id, team.name), 
                    )
                else:
                    return HttpResponse(json.dumps({'status': 'error', 'message': 'У пользователя уже есть команда или его не существует'}), content_type='application/json')
            elif user in team.want_accept.all():
                team.want_accept.remove(user)
                result = 'removed'
                team.save()
            else:
                team.want_accept.add(user)
                result = 'invited'
                team.save()
                logger.info('Team ' + str(team.id) + ' invited user ' + str(user.id))
                
                send_mail(
                    'Новое приглашение от команды', 
                    '',
                    'info@bigdata-hack.ru', 
                    [user.email], 
                    fail_silently=False, 
                    html_message = '''
                    Здравствуйте, {}! <br><br>
                    У вас новое приглашение от команды <a href="http://bigdata-hack.ru/teams/{}">{}</a>.<br>
                    Его можно посмотреть в <a href="http://bigdata-hack.ru/user/">профиле</a>.<br><br>
                    C Уважением, администрация bigdata-hack :)'''.format(user.name, team.id, team.name), 
                )
            
        return HttpResponse(json.dumps({'status': 'ok', 'result': result}), content_type='application/json')


def handle_uploaded_file(f, path):
    with open(path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def edit_avatar(request):
    logger.warning(request)
    if request.method == 'POST': #POST
        params = request.POST
        
        logger.info(request.FILES)
        logger.info(request)
        logger.info(params)
        
        if not request.user.is_authenticated(): 
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Войдите в свою учетную запись'}), content_type='application/json')  
            
        if params.get('for_team') and (not request.user.team or request.user.team.creater_id != request.user.id):
            return HttpResponse(json.dumps({'status': 'error', 'message': 'У пользователя нет команды или прав на ее редактирование'}), content_type='application/json')  
            
        if not request.FILES.get('avatar'):
            return HttpResponse(json.dumps({'status': 'error', 'message': 'Пустое поле аватарки'}), content_type='application/json')  
        
        name = str(request.FILES['avatar'].name) 
        t = None
        if name.find(".JPG", len(name) - 4) != -1 or name.find(".jpg", len(name) - 4) != -1:
            t = ".jpg"
            
        if name.find(".PNG", len(name) - 4) != -1 or name.find(".png", len(name) - 4) != -1:
            t = ".png"
            
        if name.find(".GIF", len(name) - 4) != -1 or name.find(".gif", len(name) - 4) != -1:
            t = ".gif"
            
        if t is None:
            return HttpResponse(json.dumps({'status': 'error', 'message': 'разрешаются только форматы .jpg, .png, .gif'}), content_type='application/json')  
        
        if params.get('for_team'):
            path = os.path.join(BASE_DIR, 'media/teams/' + str(request.user.team.id) + t)
            handle_uploaded_file(request.FILES['avatar'], path)
            
            request.user.team.avatar = 'teams/' + str(request.user.team.id) + t
            request.user.team.save()
            return HttpResponse(json.dumps({ 'status': 'ok', 'url': '/media/teams/' + str(request.user.team.id) + t }), content_type='application/json')
        else:        
            path = os.path.join(BASE_DIR, 'media/avatars/' + str(request.user.id) + t)
            handle_uploaded_file(request.FILES['avatar'], path)
            
            request.user.avatar = 'avatars/' + str(request.user.id) + t
            request.user.save()
            return HttpResponse(json.dumps({ 'status': 'ok', 'url': '/media/avatars/' + str(request.user.id) + t }), content_type='application/json')
        
        
