from django.shortcuts import render, redirect
from datetime import datetime
from traceback import print_tb
import json
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse
from postoapp import models, forms
from django.db.models import Q, Sum
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required

def context_data():
    context = {
        'page_name': '',
        'page_title': '',
        'system_name': 'sistema de Gestão do Posto de Combustível',
        'topbar': True,
        'footer': True,
    }

    return context

def user_register(request):
    context = context_data()
    context['topbar'] = False
    context['footer'] = False
    context['page_title'] = 'Registro de usuário'
    if request.user.is_authenticated:
        return redirect('home-page')
    return render(request, 'register.html', context)

@login_required
def upload_modal(request):
    context = context_data()
    return render(request, 'upload.html', context)

def save_register(request):
    resp = {'status': 'failed', 'msg': ''}
    if not request.method == 'POST':
        resp['msg'] = 'Nenhum dado foi enviado sobre esta solicitação'
    else:
        form = forms.SaveUser(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sua conta foi criada com sucesso')
            resp['status'] = 'success'
        else:
            for field in form:
                for error in field.errors:
                    if resp['msg'] != '':
                        resp['msg'] += str('<br />')
                    resp['msg'] += str(f'[{field.name}] {error}')

    return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required
def update_profile(request):
    context = context_data()
    context['page_title'] = 'Atualizar perfil'
    user = User.objects.get(id=request.user.id)
    if not request.method == 'POST':
        form = forms.UpdateProfile(instance=user)
        context['form'] = form
        print(form)
    else:
        form = forms.UpdateProfile(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Seu perfil foi atualizado com sucesso')
        else:
            context['form'] = form

    return render(request, 'manage_profile.html', context)

@login_required
def update_password(request):
    context = context_data()
    context['page_title'] = 'Atualizar senha'
    if request.method == 'POST':
        form = forms.UpdatePasswords(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sua senha foi atualizada com sucesso')
            return redirect('profile=page')
        else:
            form = forms.UpdatePasswords(request.POST)
            context['form'] = form
        return render(request, 'update_password.html', context)   

def login_page(request):
    context = context_data()
    context['topbar'] = False
    context['footer'] = False
    context['page_name'] = 'login'
    context['page_title'] = 'Login'
    return render(request, 'login.html', context)

def login_user(request):
    logout(request)
    resp = {'status': 'failed', 'msg': ''}
    username = ''
    password = ''
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                resp['status'] = 'success'
            else:    
                resp['msg'] = 'Nome do usuário ou senha incorretos'
        else:
            resp['msg'] = 'Nome do usuário ou senha incorretos'
    return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required
def home(request):
    context = context_data()
    context['page'] = 'Home'
    context['page_title'] = 'Home'
    context['total_type'] = models.Patrol.objects.filter(delete_flag=0, status=1).count()
    context['patrols'] = models.Patrol.objects.filter(delete_flag=0, status=1).all()
    year = datetime.now().strftime('%Y')
    month = datetime.now().strftime('%m')
    day = datetime.now().strftime('%d')
    try:
        patrols = models.Patrol.objects.filter(delete_flag=0, status=1).all().values_list('id')
        total_amount = models.Sale.objects.filter(patrol__id__in=patrols).aggregate(sum('amount'))['amount__sum']
        if total_amount is None:
            total_amount = 0
    except:
        total_amount = 0

    context['total_sales'] = total_amount

def logout_user(request):
    logout(request)
    return redirect('login-page')

@login_required
def profile(request):
    context = context_data()
    context['page'] = 'Profile'
    context['page_title'] = 'Profile'
    return render(request, 'profile.html', context)

@login_required
def patrol_list(request):
    context = context_data()
    context['page_title'] = 'Lista de tipos de gasolina'
    context['page'] = 'Patrol List'
    context['patrols'] = models.Patrol.objects.filter(delete_flag=0).all()

    return render(request, 'patrol_list.html', context)

@login_required
def manage_patrol(request, pk=None):
    context = context_data()
    context['patrol'] = {}
    if not pk is None:
        context['patrol'] = models.Patrol.objects.get(id=pk)

    return render(request, 'manage_patrol.html', context)

@login_required
def view_patrol(request, pk=None):
    context = context_data()
    context['patrol'] = {}
    if not pk is None:
        context['patrol'] = models.Patrol.objects.get(id=pk)

    return render(request, 'patrol_details.html', context)

@login_required
def save_patrol(request, pk=None):
    resp = {'status': 'failed', 'msg': ''}
    if not request.method == 'POST':
        resp['msg'] = 'Nenhum dado enviado nesta solicitação'
    else:
        post = request.POST
        if not post['id'] == '':
            petrol = models.Patrol.objects.get(id=post['id'])
            form = forms.SavePetrol(request.POST, instance=petrol)
        else:
            form = forms.SavePetrol(request.POST)
        if form.is_valid():
            form.save()
            if post['id'] == '':
                messages.success(request, 'O tipo de gasolina foi adicionado com sucesso')
            else:
                messages.success(request, 'O tipo de gasolina foi atualizado com sucesso')
            resp['status'] = 'success'
        else:
            for field in form:
                for error in field.errors:
                    if not resp['msg'] == '':
                        resp['msg'] += str('<br />')
                    resp['msg'] += str(f'[{field.label}] {error}')
    return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required
def delete_patrol(request, pk=None):
    resp = {'status': 'failed', 'msg': ''}
    if pk is None:
        resp['msg'] = 'ID de tipo de gasolina inválido'
    else:
        try:
            petrol = models.Patrol.objects.filter(id=pk).update(delete_flag=1)
            resp['status'] = 'success'
            messages.success(request, 'O tipo de gasolina foi deletado com sucesso')
        except:
            resp['msg'] = 'ID de tipo de gasolina inválido'
    return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required
def stock_list(request):
    context = context_data()
    context['page_title'] = 'Registros de ações'
    context['page'] = 'stock_list'
    petrols = models.Stock.objects.filter(delete_flag=0, status=0).all().values_list('id')
    context['stocks'] = models.Stock.objects.filter(patrol__id__in=petrols).all()

    return render(request, 'stock_list.html', context)

@login_required
def manage_stock(request, pk=None):
    context = context_data()
    context['stock'] = {}
    if not pk is None:
        context['stock'] = models.Stock.objects.get(id=pk)
    context['petrols'] = models.Petrol.objects.filter(delete_flag=0, status=1).all()
    return render(request, 'manage_stock.html', context)   

@login_required
def view_stock(request, pk=None):
    context = context_data()
    context['stock'] = {}
    if not pk is None:
        context['stock'] = models.Stock.objects.get(id=pk)

    return render(request, 'stock_details.html', context)

@login_required
def save_stock(request, pk=None):
    resp = {'status': 'failed', 'msg': ''}
    if not request.method == 'POST':
        resp['msg'] = 'Nenhum dado enviado nesta solicitação'
    else:
        post = request.POST
        if not post['id'] == '':
            stock = models.Stock.objects.get(id=post['id'])
            form = forms.SaveStock(request.POST, instance=stock)
        else:
            form = forms.SaveStock(request.POST)
        if form.is_valid():
            form.save()
            if post['id'] == '':
                messages.success(request, 'O registro de ação foi adicionado com sucesso')
            else:
                messages.success(request, 'O registro de ação foi atualizado com sucesso')
            resp['status'] = 'success'
        else:
            for field in form:
                for error in field.errors:
                    if not resp['msg'] == '':
                        resp['msg'] += str('<br />')
                    resp['msg'] += str(f'[{field.label}] {error}')
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def delete_stock(request, pk=None):
    resp = {'status': 'failed', 'msg': ''}
    if pk is None:
        resp['msg'] = 'ID de registro do estoque inválido'
    else:
        try:
            stock = models.Stock.objects.filter(id=pk).delete()
            resp['status'] = 'success'
            messages.success(request, 'O registro do estoque foi excluído com sucesso')
        except:
            resp['msg'] = 'ID de registro do estoque inválido'

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def inventary(request):
    context = context_data()
    context['page_title'] = 'Inventário'
    context['page'] = 'Inventary_page'
    context['petrols'] = models.Petrol.objects.filter(delete_flag=0, status=1).all()

    return render(request, 'inventary.html', context)

@login_required
def sale_list(request):
     context = context_data()
     context['page_title'] = 'Registros de vendas'
     context['page'] = 'sale_list'
     patrols = models.Patrol.objects.filter(delete_flag=0, status=1).all().values_list('id')

     return render(request, 'sale_list.html', context)

@login_required
def manage_sale(request, pk=None):
    context = context_data()
    context['sale'] = {}
    if not pk is None:
        context['sale'] = models.Sale.objects.get(id=pk)
    context['petrols'] = models.Petrol.objects.filter(delete_flag=0, status=1).all()
    return render(request, 'manage_sale.html', context)

@login_required
def view_sale(request, pk=None):
    context = context_data()
    context['sale'] = {}
    if not pk is None:
        context['sale'] = models.Sale.objects.get(id=pk)

    return render(request, 'view_sale.html', context)

@login_required
def save_sale(request, pk=None):
    resp = {'status': 'failed', 'msg': ''}
    if not request.method == 'POST':
        resp['msg'] = 'Nenhum dado enviado nesta aplicação'
    else:
        post = request.POST
        if not post['id'] == '':
            sale = models.Sale.objects.get(id=post['id'])
            form = forms.SaveSale(request.POST, instance=sale)
        else:
            form = forms.SaveSale(request.POST)
        if form.is_valid():
            form.save()
            if post['id'] == '':
                messages.success(request, 'O registro de venda foi adicionado com sucesso')
            else:
                messages.success(request, 'O registro de venda foi atualizado com sucesso')
            resp['status'] = 'success'
        else:
            for field in form:
                for error in field.errors:
                    if not resp['msg'] == '':
                        resp['msg'] += str('<br />')
                    resp['msg'] += str(f'[{field.label}] {error}')
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def delete_sale(request, pk=None):
    resp = {'status': 'failed', 'msg': ''}
    if pk in None:
        resp['msg'] = 'ID de registro de venda inválido'
    else:
        try:
            sale = models.Sale.objects.filter(id=pk).delete()
            messages.success(request, 'O registro de venda foi excluído com sucesso')
        except:
            resp['msg'] = 'ID de registro de venda inválido'

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def sales_report(request, rep_date=None):
    context = context_data()
    context['page_title'] = 'Relatório de vendas'
    context['page'] = 'Sale_list'
    if not rep_date is None:
        rep_date = datetime.strftime(rep_date, '%Y-%m-%d')
    else:
        rep_date = datetime.now()
    year = rep_date.strftime('%Y')
    month = rep_date.strftime('%m')
    day = rep_date.strftime('%d')
    petrols = models.Petrol.objects.filter(delete_flag=0, status=1).all().values_list('id')
    sales = models.Sale.objects.filter(patrol__id__in=petrols,
                                       date__month=month,
                                       date_day=day,
                                       date_year=year,)
    context['rep_date'] = rep_date
    context['sales'] = sales.all()
    context['total_amount'] = sales.aggregate(sum('amount'))['amount__sum']
    if context['total_amount'] is None:
        context['total_amount'] = 0

    return render(request, 'sales_report.html', context)