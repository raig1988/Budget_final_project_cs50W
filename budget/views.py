from datetime import datetime
from xxlimited import new
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from .models import *
# Decorators
from django.contrib.auth.decorators import login_required
# Password Reset libraries:
from django.contrib.auth.forms import PasswordResetForm
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.core.mail import send_mail, BadHeaderError
from django.db.models.query_utils import Q
# Aggregation functions
from django.db.models import Sum, FloatField
from django.db.models.functions import Round
# Csrf exempt
import json

def index(request):
    if request.user.is_anonymous:
        return render(request, "budget/index.html")
    elif Profile.objects.filter(user=request.user).exists():
        return render(request, "budget/index.html", {"profile" : Profile.objects.get(user=request.user)})
    return render(request, "budget/index.html")

def update_budget(request, id):
    template_budget = Budget.objects.get(user=request.user, id=id)
    selected_budget = Budget.objects.filter(user=request.user, id=id)
    if request.method == "PUT":
        data = json.loads(request.body)
        amount = data.get("amount")
        selected_budget.update(amount=amount, input_date=datetime.now())
        result_budget = Budget.objects.get(user=request.user, id=id)
        total_budget = Budget.objects.filter(user=request.user).aggregate(total_sum=Round(Sum('amount'),2))
        return JsonResponse({"message": "Budget updated successfully", "result_budget": result_budget.serialize_budget(), "new_total_budget": total_budget["total_sum"]})
    return JsonResponse({"category": template_budget.category.category, "amount": template_budget.amount})

def delete_budget(request, id):
    if request.method == "PUT":
        data = json.loads(request.body)
        budget_id = data.get("budget_id")
        selected_category = Budget.objects.get(user=request.user, id=budget_id)
        selected_category.delete()
        total_budget = Budget.objects.filter(user=request.user).aggregate(total_sum=Round(Sum('amount'),2))
        return JsonResponse({"message": "Category budget deleted sucessfully", "category": selected_category.category.category, "new_total_budget": total_budget["total_sum"]})

def add_budget(request):
    if request.method == "POST":
        data = json.loads(request.body)
        category = data.get("category")
        amount = data.get("amount")
        new_budget = Budget(user=request.user, category_id=category, amount=amount, input_date=datetime.now())
        new_budget.save()
        return JsonResponse({"message": "Budget succesfully added"})

def budget(request):
    user_budget = Budget.objects.filter(user=request.user)
    total_budget = Budget.objects.filter(user=request.user).aggregate(total_sum=Round(Sum('amount'),2))
    return JsonResponse({"budget": [item.serialize_budget() for item in user_budget], "total_budget": total_budget["total_sum"]})

def update_transaction(request, id):
    transaction_id = id
    selected_transaction = Transactions.objects.filter(user=request.user, id=transaction_id)
    template_transaction = Transactions.objects.get(user=request.user, id=transaction_id)
    if request.method == "PUT":
        # get data for date, category. description, amount
        data = json.loads(request.body)
        date = data.get("date")
        category = data.get("category")
        description = data.get('description')
        amount = data.get('amount')
        selected_transaction.update(date=date, category=category, description=description, amount=amount, input_date=datetime.now())
        result_transaction = Transactions.objects.get(user=request.user, id=transaction_id)
        return JsonResponse({"message": "Transaction update successfully.", "transaction": result_transaction.serialize_transaction() ,"day": result_transaction.date.month})
    return JsonResponse({"transaction": template_transaction.serialize_transaction(), 
        "category": template_transaction.category.id, 
        "date": template_transaction.date.strftime("%Y-%m-%d"),
        "month":template_transaction.date.month,
        "year": template_transaction.date.year 
        })

def delete_transaction(request, id):
    if request.method == "PUT":
        data = json.loads(request.body)
        transaction_id = data.get("transaction_id")
        selected_transaction = Transactions.objects.get(id=transaction_id, user=request.user)
        # delete transaction
        selected_transaction.delete()
        return JsonResponse({"data": data, "transactionMonth": selected_transaction.date.month , "transactionYear": selected_transaction.date.year})

def new_transaction(request):
    if request.method == "POST":
        # recolect data from form
        data = json.loads(request.body)
        # add data for date, category, transaction and amount
        newTransaction = Transactions(user=request.user, date=data["date"], category_id=int(data["category"]), description=data["description"], amount=data["amount"])
        newTransaction.save()
        dataTransaction = Transactions.objects.get(id=newTransaction.id)
        return JsonResponse({"message": "Post created successfully.", "dataTransactionMonth": dataTransaction.date.month, "dataTransactionYear": dataTransaction.date.year}, status=200)
    return HttpResponseNotFound('404')

def general_summary(request, date):
    year = int(request.GET['year'])
    sum_category = list(Transactions.objects.filter(user=request.user, date__year=year).values('category').annotate(categ_sum=Round(Sum('amount'),2)))
    category_dict = {}
    categories = Categories.objects.all()
    for item in categories:
        category_dict[item.id] = item.category
    monthly = list(Transactions.objects.filter(user=request.user, date__year=year).values('date__month').annotate(categ_sum=Round(Sum('amount'),2)))
    january = list(Transactions.objects.filter(user=request.user, date__month=1, date__year=year).values('category').annotate(categ_sum=Round(Sum('amount'),2)))
    february = list(Transactions.objects.filter(user=request.user, date__month=2, date__year=year).values('category').annotate(categ_sum=Sum('amount')))
    march = list(Transactions.objects.filter(user=request.user, date__month=3, date__year=year).values('category').annotate(categ_sum=Sum('amount')))
    april = list(Transactions.objects.filter(user=request.user, date__month=4, date__year=year).values('category').annotate(categ_sum=Sum('amount')))
    may = list(Transactions.objects.filter(user=request.user, date__month=5, date__year=year).values('category').annotate(categ_sum=Sum('amount')))
    june = list(Transactions.objects.filter(user=request.user, date__month=6, date__year=year).values('category').annotate(categ_sum=Sum('amount')))
    july = list(Transactions.objects.filter(user=request.user, date__month=7, date__year=year).values('category').annotate(categ_sum=Sum('amount')))
    august = list(Transactions.objects.filter(user=request.user, date__month=8, date__year=year).values('category').annotate(categ_sum=Sum('amount')))
    september = list(Transactions.objects.filter(user=request.user, date__month=9, date__year=year).values('category').annotate(categ_sum=Sum('amount')))
    october = list(Transactions.objects.filter(user=request.user, date__month=10, date__year=year).values('category').annotate(categ_sum=Sum('amount')))
    november = list(Transactions.objects.filter(user=request.user, date__month=11, date__year=year).values('category').annotate(categ_sum=Sum('amount')))
    december = list(Transactions.objects.filter(user=request.user, date__month=12, date__year=year).values('category').annotate(categ_sum=Sum('amount')))
    return JsonResponse({
        "january" : january,
        "february" : february,
        "march" : march,
        "april" : april,
        "may" : may,
        "june" : june,
        "july" : july,
        "august" : august,
        "september" : september,
        "october" : october,
        "november" : november,
        "december" : december,
        "total_monthly": monthly,
        "category_sum" : sum_category,
        "categories" : category_dict
    })

# Get summary amount per category and per month and consolidate total value
def summary_month(request, date):
    month = int(request.GET["month"])
    year = int(request.GET["year"])
    user = request.user
    array = []
    category_dict = {}
    budget_array = []
    category = Transactions.objects.filter(user=user, date__month=month, date__year=year).values('category').annotate(categ_sum=Round(Sum('amount', output_field=FloatField()), 2))
    sum_month = Transactions.objects.filter(user_id=user, date__month=month, date__year=year).aggregate(total_sum=Round(Sum('amount'),2))
    categories = Categories.objects.all()
    for item in categories:
        category_dict[item.id] = item.category
    for item in category:
        array.append(item)
    user_budget = Budget.objects.filter(user=user).values("category", "amount")
    for item in user_budget:
        budget_array.append(item)
    sum_budget = Budget.objects.filter(user=user).aggregate(total_budget_sum=Round(Sum('amount'),2))
    return JsonResponse({
        "summary" : {
            "sum_cat" : array,
            "budget" : budget_array
            },
        "total_month" : sum_month["total_sum"],
        "total_budget_month" : sum_budget["total_budget_sum"],
        "categories" : category_dict
    })

# load all transactions per user per month and year
def load_transactions(request, date):
    month = int(request.GET["month"])
    year = int(request.GET["year"])
    # pass range as year, month and day
    selected_month = Transactions.objects.filter(user=request.user, date__month=month, date__year=year)
    return JsonResponse({
        "transaction" : [transaction.serialize_transaction() for transaction in selected_month]
        })

def setnickname(request):
    if request.method == "POST":
        nickname = request.POST["nickname"]
        if not nickname:
            messages.error(request, "El nickname no puede estar vacio.")
            return redirect("index")
        if Profile.objects.filter(user=request.user).exists():
            nickname_update = Profile.objects.get(user=request.user)
            nickname_update.nickname = nickname
            nickname_update.save()
            messages.success(request, 'Tu nickname ha sido actualizado.')
            return HttpResponseRedirect(reverse("index"))
        nickname_create = Profile(user=request.user, nickname=nickname)
        nickname_create.save()
        messages.success(request, 'Tu nickname ha sido creado.')
        return HttpResponseRedirect(reverse("index"))

def change_password(request):
    if request.method == "POST":
        change_password = request.POST["changepassword"]
        confirmation_password = request.POST["confirmationpassword"]
        if not change_password:
            messages.error(request, "La contraseña no puede estar vacia.")
            return redirect("index")
        if change_password != confirmation_password:
            messages.error(request, "Las contraseñas deben coincidir.")
            return redirect("index")
        user = User.objects.get(id=request.user.id)
        user.set_password(change_password)
        user.save()
        messages.success(request, 'Tu contraseña ha sido cambiada con exito.')
        login(request, user)
        return HttpResponseRedirect(reverse("index"))

# user register, login, logout, change password

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if not password:
            return render(request, "budget/register.html", {
                "message": "La contraseña no puede estar vacia."
            })
        if password != confirmation:
            return render(request, "budget/register.html", {
                "message": "Las contraseñas deben coincidir."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "budget/register.html", {
                "message": "Nombre de usuario ya esta en uso."
            })
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "budget/register.html")

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "budget/login.html", {
                "message": "Nombre de usuario y/o contraseña invalida."
            })
    else:
        return render(request, "budget/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def password_reset_request(request):
    if request.method == 'POST':
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            selected_user = User.objects.filter(Q(email=data))
            if selected_user.exists():
                for user in selected_user:
                    subject = "Solicitud de cambio de contraseña"
                    email_template_name = "budget/password/password_reset_email.txt"
                    context_mail = {
                        "email": user.email,
                        'domain': '127.0.0.1:8000', #to be changed during production
                        'site_name' : 'AprendoFinanzas123', #to be changed during production
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'http' #to be changed during production
                    }
                    email = render_to_string(email_template_name, context_mail)
                    try:
                        send_mail(subject, email, 'aprendofinanzas123@gmail.com', [user.email], fail_silently=False) # from email to be changed during production
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
                    messages.success(request, 'Un email con las instrucciones de cambio de contraseña ha sido enviado al inbox de tu email')
                    return redirect("index")
            messages.error(request, 'El email ingresado no es valido.')
    password_reset_form = PasswordResetForm()
    return render(request, "budget/password/password_reset.html", {"password_reset_form": password_reset_form})

# end user register, login, logout, change password