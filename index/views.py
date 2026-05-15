import csv
import json
import random
import string
import re

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .models import User, Choices, Questions, Answer, Form, Responses, Establecimiento


# Create your views here.
def _get_default_redirect_for_user(user):
    if user.is_superuser:
        return reverse("index")
    if user.is_staff:
        return reverse("index")
    if user.is_active:
        return reverse("view_forms_visits")
    return reverse("403")


def _is_visit_user(user):
    return user.is_authenticated and user.is_active and not user.is_staff and not user.is_superuser


def _is_public_form_for_visit(user, form):
    if _is_visit_user(user):
        if not form.is_public:
            return False
        if not user.establecimiento:
            return False
        return form.establecimientos.filter(id=user.establecimiento_id).exists()
    return True


def _can_manage_form(user, form):
    return user.is_superuser or form.creator_id == user.id


@login_required(login_url="login")
def index(request):
    if request.user.is_superuser:
        forms = Form.objects.all()
    else:
        forms = Form.objects.filter(creator=request.user)
    return render(request, "index/index.html", {
        "forms": forms
    })

@login_required(login_url="login")
def view_forms_visits(request):

    if request.user.is_superuser or request.user.is_staff or not request.user.is_active:
        return HttpResponseRedirect(reverse("403"))

    responded_form_ids = Responses.objects.filter(
        responder=request.user
    ).values_list("response_to_id", flat=True).distinct()

    user_establecimiento = request.user.establecimiento

    visible_forms = Form.objects.filter(
        is_public=True,
        establecimientos=user_establecimiento,
    ).exclude(
        creator=request.user
    ).distinct()

    responded_forms = visible_forms.filter(
        id__in=responded_form_ids
    ).order_by("title")

    available_forms = visible_forms.exclude(
        id__in=responded_form_ids
    ).order_by("title")

    return render(request, "index/view_forms_visits.html", {
        "responded_forms": responded_forms,
        "available_forms": available_forms,
    })


@login_required(login_url="login")
def view_visit_response(request, code):

    if request.user.is_superuser or request.user.is_staff or not request.user.is_active:
        return HttpResponseRedirect(reverse("403"))

    form_info = Form.objects.filter(code=code).first()
    if not form_info:
        return HttpResponseRedirect(reverse("404"))

    if not _is_public_form_for_visit(request.user, form_info):
        return HttpResponseRedirect(reverse("403"))

    response_info = Responses.objects.filter(
        response_to=form_info,
        responder=request.user
    ).prefetch_related("response__answer_to", "response__answer_to__choices").first()

    if not response_info:
        return HttpResponseRedirect(reverse("already_voted", args=[code]))

    return render(request, "index/view_visit_response.html", {
        "form": form_info,
        "response": response_info,
        "visit_user": request.user,
        "establecimiento": request.user.establecimiento,
    })


def login_view(request):
    # Check if the user is logged in
    if request.user.is_authenticated:
        return HttpResponseRedirect(_get_default_redirect_for_user(request.user))
    if request.method == "POST":
        username = request.POST["username"].upper()
        password = request.POST["password"]
        next_url = request.POST.get("next") or request.GET.get("next")
        user = authenticate(request, username=username, password=password)
        # if user authentication success
        if user is not None:
            login(request, user)
            is_form_user = user.is_active and not user.is_staff and not user.is_superuser
            form_user_allowed_next = [
                re.compile(r"^/forms/visits$"),
                re.compile(r"^/form/[^/]+/viewform$"),
                re.compile(r"^/form/[^/]+/submit$"),
                re.compile(r"^/form/[^/]+/response/[^/]+/edit$"),
                re.compile(r"^/form/[^/]+/already-voted$"),
                re.compile(r"^/form/[^/]+/my-response$"),
                re.compile(r"^/logout$"),
                re.compile(r"^/403$"),
                re.compile(r"^/404$"),
            ]

            if next_url and (not is_form_user or any(pattern.match(next_url) for pattern in form_user_allowed_next)):
                return HttpResponseRedirect(next_url)
            return HttpResponseRedirect(_get_default_redirect_for_user(user))
        else:
            return render(request, "index/login.html", {
                "message": "Credenciales inválidas.",
                "next": next_url
            })
    return render(request, "index/login.html", {
        "next": request.GET.get("next", "")
    })


def register(request):
    # Check if the user is logged in
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('index'))
    if request.method == "POST":
        username = request.POST["username"].lower()
        password = request.POST["password"]
        email = request.POST["email"]
        confirmation = request.POST["confirmation"]
        # check if the password is the same as confirmation
        if password != confirmation:
            return render(request, "index/register.html", {
                "message": "Passwords must match."
            })
        # Checks if the username is already in use
        if User.objects.filter(email=email).count() == 1:
            return render(request, "index/register.html", {
                "message": "Email already taken."
            })
        try:
            user = User.objects.create_user(username=username, password=password, email=email)
            user.save()
            login(request, user)
            return HttpResponseRedirect(reverse('index'))
        except IntegrityError:
            return render(request, "index/register.html", {
                "message": "Username already taken"
            })
    return render(request, "index/register.html")


def _render_users_management(request, message=None, message_type="danger", form_data=None):
    username = request.GET.get("username", "").strip()
    first_name = request.GET.get("first_name", "").strip()
    last_name = request.GET.get("last_name", "").strip()
    establecimiento = request.GET.get("establecimiento", "").strip()
    estado = request.GET.get("estado", "").strip()

    users = User.objects.all().order_by("username")
    if username:
        users = users.filter(username__icontains=username)
    if first_name:
        users = users.filter(first_name__icontains=first_name)
    if last_name:
        users = users.filter(last_name__icontains=last_name)
    if establecimiento:
        users = users.filter(establecimiento_id=establecimiento)
    if estado == "activo":
        users = users.filter(is_active=True)
    elif estado == "inactivo":
        users = users.filter(is_active=False)

    paginator = Paginator(users, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    establecimientos = Establecimiento.objects.select_related("comuna").order_by("nombre")

    return render(request, "index/create_user.html", {
        "users": page_obj.object_list,
        "page_obj": page_obj,
        "establecimientos": establecimientos,
        "filters": {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "establecimiento": establecimiento,
            "estado": estado,
        },
        "total_users": users.count(),
        "message": message,
        "message_type": message_type,
        "form_data": form_data or {}
    })


@login_required(login_url="login")
def list_users(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return HttpResponseRedirect(reverse("403"))
    return _render_users_management(request)


@login_required(login_url="login")
def create_user(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return HttpResponseRedirect(reverse("403"))
    if request.method != "POST":
        return HttpResponseRedirect(reverse("create_user"))

    username = request.POST.get("username", "").strip().lower()
    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()
    password = request.POST.get("password", "")
    email = request.POST.get("email", "").strip().lower()
    confirmation = request.POST.get("confirmation", "")
    establecimiento_id = request.POST.get("establecimiento", "").strip()
    is_active = request.POST.get("is_active") == "on"
    is_staff = request.POST.get("is_staff") == "on"
    form_data = {
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "establecimiento": establecimiento_id,
        "is_active": is_active,
        "is_staff": is_staff
    }

    if not username or not first_name or not last_name or not password or not email or not confirmation or not establecimiento_id:
        return _render_users_management(request, "Todos los campos son obligatorios.", "danger", form_data)
    if password != confirmation:
        return _render_users_management(request, "Las contraseñas no coinciden.", "danger", form_data)
    if User.objects.filter(email=email).exists():
        return _render_users_management(request, "El correo ya está registrado.", "danger", form_data)
    if User.objects.filter(username=username).exists():
        return _render_users_management(request, "El nombre de usuario ya existe.", "danger", form_data)

    establecimiento = Establecimiento.objects.filter(pk=establecimiento_id).first()
    if not establecimiento:
        return _render_users_management(request, "El establecimiento seleccionado no es válido.", "danger", form_data)

    try:
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            email=email,
            establecimiento=establecimiento,
            is_staff=is_staff,
            is_superuser=False,
            is_active=is_active
        )
        user.save()
        return HttpResponseRedirect(f"{reverse('create_user')}?created=1")
    except IntegrityError:
        return _render_users_management(request, "No se pudo crear el usuario.", "danger", form_data)


@login_required(login_url="login")
def update_user(request, user_id):
    if not request.user.is_staff and not request.user.is_superuser:
        return HttpResponseRedirect(reverse("403"))

    user = User.objects.filter(pk=user_id).first()
    if not user:
        return HttpResponseRedirect(f"{reverse('create_user')}?error=user_not_found")

    establecimientos = Establecimiento.objects.select_related("comuna").order_by("nombre")

    if request.method == "POST":
        username = request.POST.get("username", "").strip().lower()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        establecimiento_id = request.POST.get("establecimiento", "").strip()
        is_active = request.POST.get("is_active") == "on"
        is_staff = request.POST.get("is_staff") == "on"

        if not username or not first_name or not last_name or not email or not establecimiento_id:
            return render(request, "index/update_user.html", {
                "user_to_edit": user,
                "establecimientos": establecimientos,
                "message": "Usuario, nombre, apellido, correo y establecimiento son obligatorios.",
                "message_type": "danger"
            })

        if User.objects.exclude(pk=user.pk).filter(username=username).exists():
            return render(request, "index/update_user.html", {
                "user_to_edit": user,
                "establecimientos": establecimientos,
                "message": "El nombre de usuario ya existe.",
                "message_type": "danger"
            })

        if User.objects.exclude(pk=user.pk).filter(email=email).exists():
            return render(request, "index/update_user.html", {
                "user_to_edit": user,
                "establecimientos": establecimientos,
                "message": "El correo ya está registrado.",
                "message_type": "danger"
            })

        establecimiento = Establecimiento.objects.filter(pk=establecimiento_id).first()
        if not establecimiento:
            return render(request, "index/update_user.html", {
                "user_to_edit": user,
                "establecimientos": establecimientos,
                "message": "El establecimiento seleccionado no es válido.",
                "message_type": "danger"
            })

        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.establecimiento = establecimiento
        user.is_active = is_active
        user.is_staff = is_staff
        user.save()
        return HttpResponseRedirect(f"{reverse('create_user')}?updated=1")

    return render(request, "index/update_user.html", {
        "user_to_edit": user,
        "establecimientos": establecimientos
    })


@login_required(login_url="login")
def reset_user_password(request, user_id):
    if not request.user.is_staff and not request.user.is_superuser:
        return HttpResponseRedirect(reverse("403"))

    user = User.objects.filter(pk=user_id).first()
    if not user:
        return HttpResponseRedirect(f"{reverse('create_user')}?error=user_not_found")

    if request.method == "POST":
        password = request.POST.get("password", "")
        confirmation = request.POST.get("confirmation", "")

        if not password or not confirmation:
            return render(request, "index/reset_user_password.html", {
                "user_to_edit": user,
                "message": "Todos los campos son obligatorios.",
                "message_type": "danger"
            })

        if password != confirmation:
            return render(request, "index/reset_user_password.html", {
                "user_to_edit": user,
                "message": "Las contraseñas no coinciden.",
                "message_type": "danger"
            })

        user.set_password(password)
        user.save()
        return HttpResponseRedirect(f"{reverse('create_user')}?password_reset=1")

    return render(request, "index/reset_user_password.html", {
        "user_to_edit": user
    })


def logout_view(request):
    # Logout the user
    logout(request)
    next_url = request.GET.get("next", "").strip()
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return HttpResponseRedirect(next_url)
    return HttpResponseRedirect(reverse('index'))


@login_required(login_url="login")
def create_form(request):
    # Create a blank form API
    if request.method == "POST":
        data = json.loads(request.body)
        title = data["title"]
        code = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(30))
        choices = Choices(choice="Option 1")
        choices.save()
        question = Questions(question_type="multiple choice", question="Untitled Question", required=False)
        question.save()
        question.choices.add(choices)
        question.save()
        form = Form(code=code, title=title, creator=request.user)
        form.save()
        form.questions.add(question)
        form.save()
        return JsonResponse({"message": "Sucess", "code": code})


@login_required(login_url="login")
def edit_form(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse("404"))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    return render(request, "index/form.html", {
        "code": code,
        "form": formInfo,
        "establecimientos": Establecimiento.objects.all().order_by("nombre"),
        'section': 'questions'
    })


@login_required(login_url="login")
def edit_title(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse("404"))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if request.method == "POST":
        data = json.loads(request.body)
        if len(data["title"]) > 0:
            formInfo.title = data["title"]
            formInfo.save()
        else:
            formInfo.title = formInfo.title[0]
            formInfo.save()
        return JsonResponse({"message": "Success", "title": formInfo.title})


@login_required(login_url="login")
def edit_description(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse("404"))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if request.method == "POST":
        data = json.loads(request.body)
        formInfo.description = data["description"]
        formInfo.save()
        return JsonResponse({"message": "Success", "description": formInfo.description})


@login_required(login_url="login")
def edit_bg_color(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse("404"))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if request.method == "POST":
        data = json.loads(request.body)
        formInfo.background_color = data["bgColor"]
        formInfo.save()
        return JsonResponse({"message": "Success", "bgColor": formInfo.background_color})


@login_required(login_url="login")
def edit_text_color(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse("404"))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if request.method == "POST":
        data = json.loads(request.body)
        formInfo.text_color = data["textColor"]
        formInfo.save()
        return JsonResponse({"message": "Success", "textColor": formInfo.text_color})


@login_required(login_url="login")
def edit_setting(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse("404"))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if request.method == "POST":
        data = json.loads(request.body)
        establecimiento_ids = data.get("establecimientos", [])

        formInfo.collect_email = data.get("collect_email", formInfo.collect_email)
        formInfo.is_quiz = data.get("is_quiz", formInfo.is_quiz)
        formInfo.is_public = data.get("is_public", formInfo.is_public)
        formInfo.authenticated_responder = data.get("authenticated_responder", formInfo.authenticated_responder)
        formInfo.confirmation_message = data.get("confirmation_message", formInfo.confirmation_message)
        formInfo.edit_after_submit = data.get("edit_after_submit", formInfo.edit_after_submit)
        formInfo.allow_view_score = data.get("allow_view_score", formInfo.allow_view_score)
        formInfo.save()
        establecimientos = Establecimiento.objects.filter(id__in=establecimiento_ids)
        formInfo.establecimientos.set(establecimientos)
        return JsonResponse({'message': "Success"})


@login_required(login_url="login")
def delete_form(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse("404"))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if request.method == "DELETE":
        # Delete all questions and choices
        for i in formInfo.questions.all():
            for j in i.choices.all():
                j.delete()
            i.delete()
        for i in Responses.objects.filter(response_to=formInfo):
            for j in i.response.all():
                j.delete()
            i.delete()
        formInfo.delete()
        return JsonResponse({'message': "Success"})


@login_required(login_url="login")
def edit_question(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if request.method == "POST":
        data = json.loads(request.body)
        question_id = data["id"]
        question = Questions.objects.filter(id=question_id)
        if question.count() == 0:
            return HttpResponseRedirect(reverse("404"))
        else:
            question = question[0]
        question.question = data["question"]
        question.question_type = data["question_type"]
        question.required = data["required"]
        if (data.get("score")): question.score = data["score"]
        if (data.get("answer_key")): question.answer_key = data["answer_key"]
        question.save()
        return JsonResponse({'message': "Success"})


@login_required(login_url="login")
def edit_choice(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if request.method == "POST":
        data = json.loads(request.body)
        choice_id = data["id"]
        choice = Choices.objects.filter(id=choice_id)
        if choice.count() == 0:
            return HttpResponseRedirect(reverse("404"))
        else:
            choice = choice[0]
        choice.choice = data["choice"]
        if (data.get('is_answer')): choice.is_answer = data["is_answer"]
        choice.save()
        return JsonResponse({'message': "Success"})


@login_required(login_url="login")
def add_choice(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if request.method == "POST":
        data = json.loads(request.body)
        choice = Choices(choice="Option")
        choice.save()
        formInfo.questions.get(pk=data["question"]).choices.add(choice)
        formInfo.save()
        return JsonResponse({"message": "Success", "choice": choice.choice, "id": choice.id})


@login_required(login_url="login")
def remove_choice(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if request.method == "POST":
        data = json.loads(request.body)
        choice = Choices.objects.filter(pk=data["id"])
        if choice.count() == 0:
            return HttpResponseRedirect(reverse("404"))
        else:
            choice = choice[0]
        choice.delete()
        return JsonResponse({"message": "Success"})


@login_required(login_url="login")
def get_choice(request, code, question):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if request.method == "GET":
        question = Questions.objects.filter(id=question)
        if question.count() == 0:
            return HttpResponseRedirect(reverse('404'))
        else:
            question = question[0]
        choices = question.choices.all()
        choices = [{"choice": i.choice, "is_answer": i.is_answer, "id": i.id} for i in choices]
        return JsonResponse({"choices": choices, "question": question.question, "question_type": question.question_type,
                             "question_id": question.id})


@login_required(login_url="login")
def add_question(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if request.method == "POST":
        choices = Choices(choice="Option 1")
        choices.save()
        question = Questions(question_type="multiple choice", question="Untitled Question", required=False)
        question.save()
        question.choices.add(choices)
        question.save()
        formInfo.questions.add(question)
        formInfo.save()
        return JsonResponse({'question': {'question': "Nueva Pregunta", "question_type": "multiple choice",
                                          "required": False, "id": question.id},
                             "choices": {"choice": "Option 1", "is_answer": False, 'id': choices.id}})


@login_required(login_url="login")
def delete_question(request, code, question):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if request.method == "DELETE":
        question = formInfo.questions.filter(id=question)
        if question.count() == 0:
            return HttpResponseRedirect(reverse("404"))
        else:
            question = question[0]
        for answer in Answer.objects.filter(answer_to=question):
            answer.delete()
        for i in question.choices.all():
            i.delete()
        question.delete()
        return JsonResponse({"message": "Success"})


@login_required(login_url="login")
def score(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if not formInfo.is_quiz:
        return HttpResponseRedirect(reverse("edit_form", args=[code]))
    else:
        return render(request, "index/score.html", {
            "form": formInfo
        })


@login_required(login_url="login")
def edit_score(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if not formInfo.is_quiz:
        return HttpResponseRedirect(reverse("edit_form", args=[code]))
    else:
        if request.method == "POST":
            data = json.loads(request.body)
            question_id = data["question_id"]
            question = formInfo.questions.filter(id=question_id)
            if question.count() == 0:
                return HttpResponseRedirect(reverse("edit_form", args=[code]))
            else:
                question = question[0]
            score = data["score"]
            if score == "": score = 0
            question.score = score
            question.save()
            return JsonResponse({"message": "Success"})


@login_required(login_url="login")
def answer_key(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if not formInfo.is_quiz:
        return HttpResponseRedirect(reverse("edit_form", args=[code]))
    else:
        if request.method == "POST":
            data = json.loads(request.body)
            question = Questions.objects.filter(id=data["question_id"])
            if question.count() == 0:
                return HttpResponseRedirect(reverse("edit_form", args=[code]))
            else:
                question = question[0]
            if question.question_type == "short" or question.question_type == "paragraph":
                question.answer_key = data["answer_key"]
                question.save()
            else:
                for i in question.choices.all():
                    i.is_answer = False
                    i.save()
                if question.question_type == "multiple choice":
                    choice = question.choices.get(pk=data["answer_key"])
                    choice.is_answer = True
                    choice.save()
                else:
                    for i in data["answer_key"]:
                        choice = question.choices.get(id=i)
                        choice.is_answer = True
                        choice.save()
                question.save()
            return JsonResponse({'message': "Success"})


@login_required(login_url="login")
def feedback(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if not formInfo.is_quiz:
        return HttpResponseRedirect(reverse("edit_form", args=[code]))
    else:
        if request.method == "POST":
            data = json.loads(request.body)
            question = formInfo.questions.get(id=data["question_id"])
            question.feedback = data["feedback"]
            question.save()
            return JsonResponse({'message': "Success"})


@login_required(login_url="login")
def view_form(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        formInfo = formInfo[0]
    if not _is_public_form_for_visit(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if request.user.is_authenticated and formInfo.authenticated_responder:
        if Responses.objects.filter(response_to=formInfo, responder=request.user).exists():
            logout(request)
            return HttpResponseRedirect(reverse("login"))
    if formInfo.authenticated_responder:
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse("login"))
    response = render(request, "index/view_form.html", {
        "form": formInfo
    })
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def _validate_form_submission_data(form_info, post_data):
    email_value = ""
    if form_info.collect_email:
        email_value = post_data.get("email-address", "").strip()
        if not email_value:
            return None, None, "El correo electrónico es obligatorio."
        if len(email_value) > Responses._meta.get_field("responder_email").max_length:
            return None, None, "El correo electrónico es demasiado largo."
        try:
            validate_email(email_value)
        except ValidationError:
            return None, None, "El correo electrónico no es válido."

    question_ids = {str(question.id) for question in form_info.questions.all()}
    allowed_post_keys = question_ids | {"csrfmiddlewaretoken", "email-address"}
    invalid_post_keys = [key for key in post_data.keys() if key not in allowed_post_keys]
    if invalid_post_keys:
        return None, None, "Se recibieron preguntas inválidas."

    cleaned_answers = {}
    answer_max_length = Answer._meta.get_field("answer").max_length

    for question in form_info.questions.all():
        raw_values = [value.strip() for value in post_data.getlist(str(question.id)) if value.strip() != ""]

        if question.question_type in ["short", "paragraph"]:
            if len(raw_values) > 1:
                return None, None, "Formato de respuesta inválido."
            answer_value = raw_values[0] if raw_values else ""
            if question.required and answer_value == "":
                return None, None, "Faltan respuestas obligatorias."
            if answer_value and len(answer_value) > answer_max_length:
                return None, None, "Una respuesta excede el largo máximo permitido."
            if answer_value:
                cleaned_answers[question.id] = [answer_value]

        elif question.question_type == "multiple choice":
            if len(raw_values) > 1:
                return None, None, "Solo se permite una opción por pregunta."
            if question.required and len(raw_values) == 0:
                return None, None, "Faltan respuestas obligatorias."
            if not raw_values:
                continue
            selected_value = raw_values[0]
            if not selected_value.isdigit():
                return None, None, "Opción inválida enviada."
            allowed_choice_ids = {str(choice_id) for choice_id in question.choices.values_list("id", flat=True)}
            if selected_value not in allowed_choice_ids:
                return None, None, "Opción inválida enviada."
            cleaned_answers[question.id] = [selected_value]

        elif question.question_type == "checkbox":
            if question.required and len(raw_values) == 0:
                return None, None, "Faltan respuestas obligatorias."
            if not raw_values:
                continue
            allowed_choice_ids = {str(choice_id) for choice_id in question.choices.values_list("id", flat=True)}
            selected_values = []
            selected_set = set()
            for value in raw_values:
                if not value.isdigit() or value not in allowed_choice_ids:
                    return None, None, "Opción inválida enviada."
                if value in selected_set:
                    continue
                selected_set.add(value)
                selected_values.append(value)
            cleaned_answers[question.id] = selected_values

        else:
            return None, None, "Tipo de pregunta no soportado."

    return cleaned_answers, email_value, None


def _resolve_recipient_email(request, form_info, email_value):
    if request.user.is_authenticated and request.user.email:
        return request.user.email
    if form_info.collect_email and email_value:
        return email_value
    return ""


def _build_answers_for_email(form_info, cleaned_answers):
    answers_for_email = []
    questions_by_id = {question.id: question for question in form_info.questions.all()}

    for question in form_info.questions.all():
        selected_answers = cleaned_answers.get(question.id, [])
        if not selected_answers:
            display_answers = ["Sin respuesta"]
        elif question.question_type in ["multiple choice", "checkbox"]:
            choices_by_id = {str(choice.id): choice.choice for choice in question.choices.all()}
            display_answers = [choices_by_id.get(str(answer_id), "Opción no encontrada") for answer_id in selected_answers]
        else:
            display_answers = selected_answers

        answers_for_email.append({
            "question": question.question,
            "answers": display_answers,
            "required": question.required
        })

    return answers_for_email, questions_by_id


def _build_submission_email_context(request, form_info, answers_for_email, recipient_email=""):
    voter_name = ""
    voter_rut = "No informado"
    voter_email = recipient_email or "No informado"
    voter_establecimiento = "No informado"

    if request.user.is_authenticated:
        voter_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        voter_rut = request.user.username or "No informado"
        voter_email = request.user.email or recipient_email or "No informado"
        if request.user.establecimiento:
            voter_establecimiento = str(request.user.establecimiento)

    return {
        "form": form_info,
        "voter_name": voter_name,
        "voter_rut": voter_rut,
        "voter_email": voter_email,
        "voter_establecimiento": voter_establecimiento,
        "answers_for_email": answers_for_email,
        "submitted_at": timezone.localtime(),
    }


def _send_submission_email(request, form_info, cleaned_answers, email_value):
    recipient_email = _resolve_recipient_email(request, form_info, email_value)
    if not recipient_email:
        return

    answers_for_email, _ = _build_answers_for_email(form_info, cleaned_answers)
    context = _build_submission_email_context(request, form_info, answers_for_email, recipient_email)

    html_content = render_to_string("index/emails/submission_confirmation.html", context)
    subject = f"Confirmación de envío - {form_info.title}"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@localhost")

    email_message = EmailMultiAlternatives(
        subject=subject,
        body="Hemos recibido tu formulario. Revisa la versión HTML de este correo para ver el detalle de tus respuestas.",
        from_email=from_email,
        to=[recipient_email],
    )
    email_message.attach_alternative(html_content, "text/html")
    email_message.send(fail_silently=True)


@login_required(login_url="login")
def preview_submission_confirmation(request):
    if request.user.is_superuser:
        form_info = Form.objects.order_by("-id").first()
    else:
        form_info = Form.objects.filter(creator=request.user).order_by("-id").first()

    if form_info:
        answers_for_email = []
        for question in form_info.questions.all():
            if question.question_type in ["multiple choice", "checkbox"]:
                first_choice = question.choices.first()
                display_answers = [first_choice.choice] if first_choice else ["Sin respuesta"]
            else:
                display_answers = ["Respuesta de ejemplo"]

            answers_for_email.append({
                "question": question.question,
                "answers": display_answers,
                "required": question.required
            })
    else:
        form_info = {"title": "Formulario de ejemplo"}
        answers_for_email = [
            {
                "question": "Pregunta de ejemplo",
                "answers": ["Respuesta de ejemplo"],
                "required": False
            }
        ]

    context = _build_submission_email_context(request, form_info, answers_for_email)
    return render(request, "index/emails/submission_confirmation.html", context)


def submit_form(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        formInfo = formInfo[0]
    if not _is_public_form_for_visit(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if request.user.is_authenticated and Responses.objects.filter(response_to=formInfo, responder=request.user).exists():
        if formInfo.authenticated_responder:
            logout(request)
            return HttpResponseRedirect(reverse("login"))
        return HttpResponseRedirect(reverse("already_voted", args=[code]))
    if formInfo.authenticated_responder:
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse("login"))
    if request.method == "POST":
        cleaned_answers, email_value, validation_error = _validate_form_submission_data(formInfo, request.POST)
        if validation_error:
            return HttpResponse(validation_error, status=400)

        response_code = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(20))
        response_data = {
            "response_code": response_code,
            "response_to": formInfo,
            "responder_ip": get_client_ip(request)
        }
        if request.user.is_authenticated:
            response_data["responder"] = request.user
        if formInfo.collect_email:
            response_data["responder_email"] = email_value

        response = Responses(**response_data)
        response.save()
        questions_by_id = {question.id: question for question in formInfo.questions.all()}
        for question_id, question_answers in cleaned_answers.items():
            question = questions_by_id.get(question_id)
            if not question:
                return HttpResponse("Pregunta inválida.", status=400)
            for answer_value in question_answers:
                answer = Answer(answer=answer_value, answer_to=question)
                answer.save()
                response.response.add(answer)
                response.save()

        _send_submission_email(request, formInfo, cleaned_answers, email_value)

        return render(request, "index/form_response.html", {
            "form": formInfo,
            "code": response_code,
            "auto_logout": formInfo.authenticated_responder and request.user.is_authenticated,
        })


@login_required(login_url="login")
def already_voted(request, code):
    formInfo = Form.objects.filter(code=code)
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    return render(request, "index/already_voted.html", {
        "form": formInfo[0]
    })


@login_required(login_url="login")
def responses(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        formInfo = formInfo[0]

    responsesSummary = []
    choiceAnswered = {}
    filteredResponsesSummary = {}
    for question in formInfo.questions.all():
        answers = Answer.objects.filter(answer_to=question.id)
        if question.question_type == "multiple choice" or question.question_type == "checkbox":
            choiceAnswered[question.question] = choiceAnswered.get(question.question, {})
            for answer in answers:
                choice = answer.answer_to.choices.get(id=answer.answer).choice
                choiceAnswered[question.question][choice] = choiceAnswered.get(question.question, {}).get(choice, 0) + 1
        responsesSummary.append({"question": question, "answers": answers})
    for answr in choiceAnswered:
        filteredResponsesSummary[answr] = {}
        keys = choiceAnswered[answr].values()
        for choice in choiceAnswered[answr]:
            filteredResponsesSummary[answr][choice] = choiceAnswered[answr][choice]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    return render(request, "index/responses.html", {
        "form": formInfo,
        "responses": Responses.objects.filter(response_to=formInfo),
        "responsesSummary": responsesSummary,
        "filteredResponsesSummary": filteredResponsesSummary,
        "establecimientos": Establecimiento.objects.all().order_by("nombre"),
        'section': 'responses'
    })


def retrieve_checkbox_choices(response, question):
    checkbox_answers = []

    answers = Answer.objects.filter(answer_to=question, response=response)
    for answer in answers:
        selected_choice_ids = answer.answer.split(',')  # Split the string into individual choice IDs
        selected_choices = Choices.objects.filter(pk__in=selected_choice_ids)
        checkbox_answers.append([choice.choice for choice in selected_choices])

    return checkbox_answers


@login_required(login_url="login")
def exportcsv(request, code):
    formInfo = Form.objects.filter(code=code)
    formInfo = formInfo[0]
    responses = Responses.objects.filter(response_to=formInfo)
    questions = formInfo.questions.all()

    http_response = HttpResponse()
    http_response['Content-Disposition'] = f'attachment; filename= {formInfo.title}.csv'
    writer = csv.writer(http_response)
    header = ['Response Code', 'Responder', 'Responder Email', 'Responder_ip']

    for question in questions:
        header.append(question.question)

    writer.writerow(header)

    for response in responses:
        response_data = [
            response.response_code,
            response.responder.username if response.responder else 'Anonymous',
            response.responder_email if response.responder_email else '',
            response.responder_ip if response.responder_ip else ''
        ]
        for question in questions:
            answer = Answer.objects.filter(answer_to=question, response=response).first()

            if question.question_type not in ['multiple choice', 'checkbox']:
                response_data.append(answer.answer if answer else '')
            elif question.question_type == "multiple choice":
                response_data.append(answer.answer_to.choices.get(id=answer.answer).choice if answer else '')
            elif question.question_type == "checkbox":
                if answer and question.question_type == 'checkbox':
                    checkbox_choices = retrieve_checkbox_choices(response, answer.answer_to)
                    response_data.append(checkbox_choices)

        print(response_data)
        writer.writerow(response_data)

    return http_response


def response(request, code, response_code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not formInfo.allow_view_score:
        if not _can_manage_form(request.user, formInfo):
            return HttpResponseRedirect(reverse("403"))
    total_score = 0
    score = 0
    responseInfo = Responses.objects.filter(response_code=response_code)
    if responseInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        responseInfo = responseInfo[0]
    if formInfo.is_quiz:
        for i in formInfo.questions.all():
            total_score += i.score
        for i in responseInfo.response.all():
            if i.answer_to.question_type == "short" or i.answer_to.question_type == "paragraph":
                if i.answer == i.answer_to.answer_key: score += i.answer_to.score
            elif i.answer_to.question_type == "multiple choice":
                answerKey = None
                for j in i.answer_to.choices.all():
                    if j.is_answer: answerKey = j.id
                if answerKey is not None and int(answerKey) == int(i.answer):
                    score += i.answer_to.score
        _temp = []
        for i in responseInfo.response.all():
            if i.answer_to.question_type == "checkbox" and i.answer_to.pk not in _temp:
                answers = []
                answer_keys = []
                for j in responseInfo.response.filter(answer_to__pk=i.answer_to.pk):
                    answers.append(int(j.answer))
                    for k in j.answer_to.choices.all():
                        if k.is_answer and k.pk not in answer_keys: answer_keys.append(k.pk)
                    _temp.append(i.answer_to.pk)
                if answers == answer_keys: score += i.answer_to.score
    return render(request, "index/response.html", {
        "form": formInfo,
        "response": responseInfo,
        "score": score,
        "total_score": total_score
    })


def edit_response(request, code, response_code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        formInfo = formInfo[0]
    response = Responses.objects.filter(response_code=response_code, response_to=formInfo)
    if response.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        response = response[0]
    if formInfo.authenticated_responder:
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse("login"))
        if response.responder != request.user:
            return HttpResponseRedirect(reverse('403'))
    if request.method == "POST":
        cleaned_answers, email_value, validation_error = _validate_form_submission_data(formInfo, request.POST)
        if validation_error:
            return HttpResponse(validation_error, status=400)

        if formInfo.authenticated_responder and not response.responder:
            response.responder = request.user
            response.save()
        if formInfo.collect_email:
            response.responder_email = email_value
            response.save()
        # Deleting all existing answers
        for i in response.response.all():
            i.delete()
        questions_by_id = {question.id: question for question in formInfo.questions.all()}
        for question_id, question_answers in cleaned_answers.items():
            question = questions_by_id.get(question_id)
            if not question:
                return HttpResponse("Pregunta inválida.", status=400)
            for answer_value in question_answers:
                answer = Answer(answer=answer_value, answer_to=question)
                answer.save()
                response.response.add(answer)
                response.save()
        if formInfo.is_quiz:
            return HttpResponseRedirect(reverse("response", args=[formInfo.code, response.response_code]))
        else:
            return render(request, "index/form_response.html", {
                "form": formInfo,
                "code": response.response_code
            })
    return render(request, "index/edit_response.html", {
        "form": formInfo,
        "response": response
    })


@login_required(login_url="login")
def contact_form_template(request):
    # Create a blank form API
    if request.method == "POST":
        code = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(30))
        name = Questions(question_type="short", question="Nombre Completo", required=True)
        name.save()
        email = Questions(question_type="short", question="Correo Electrónico", required=True)
        email.save()
        address = Questions(question_type="paragraph", question="Dirección", required=True)
        address.save()
        phone = Questions(question_type="short", question="Número de Teléfono", required=False)
        phone.save()
        comments = Questions(question_type="paragraph", question="Comentarios", required=False)
        comments.save()
        form = Form(code=code, title="Información de Contacto", creator=request.user, background_color="#e2eee0",
                    allow_view_score=False, edit_after_submit=True)
        form.save()
        form.questions.add(name)
        form.questions.add(email)
        form.questions.add(address)
        form.questions.add(phone)
        form.questions.add(comments)
        form.save()
        return JsonResponse({"message": "Sucess", "code": code})


@login_required(login_url="login")
def customer_feedback_template(request):
    # Create a blank form API
    if request.method == "POST":
        code = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(30))
        comment = Choices(choice="Comentarios")
        comment.save()
        question = Choices(choice="Preguntas")
        question.save()
        bug = Choices(choice="Reporte de Fallas")
        bug.save()
        feature = Choices(choice="Solicitud de función")
        feature.save()
        feedback_type = Questions(question="Tipo de comentario", question_type="multiple choice", required=False)
        feedback_type.save()
        feedback_type.choices.add(comment)
        feedback_type.choices.add(bug)
        feedback_type.choices.add(question)
        feedback_type.choices.add(feature)
        feedback_type.save()
        feedback = Questions(question="Comentario", question_type="paragraph", required=True)
        feedback.save()
        suggestion = Questions(question="Sugerencias para mejorar", question_type="paragraph", required=False)
        suggestion.save()
        name = Questions(question="Nombre Completo", question_type="short", required=False)
        name.save()
        email = Questions(question="Correo Electrónico", question_type="short", required=False)
        email.save()
        form = Form(code=code, title="Comentarios de los clientes", creator=request.user, background_color="#e2eee0",
                    confirmation_message="¡Muchas gracias por darnos tu opinión!",
                    description="¡Nos encantaría conocer tus opiniones o comentarios sobre cómo podemos mejorar tu experiencia!",
                    allow_view_score=False, edit_after_submit=True)
        form.save()
        form.questions.add(feedback_type)
        form.questions.add(feedback)
        form.questions.add(suggestion)
        form.questions.add(name)
        form.questions.add(email)
        return JsonResponse({"message": "Sucess", "code": code})


@login_required(login_url="login")
def event_registration_template(request):
    # Create a blank form API
    if request.method == "POST":
        code = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(30))
        name = Questions(question="Nombre Completo", question_type="short", required=False)
        name.save()
        email = Questions(question="Correo Electrónico", question_type="short", required=True)
        email.save()
        organization = Questions(question="Organización", question_type="short", required=True)
        organization.save()
        day1 = Choices(choice="Día 1")
        day1.save()
        day2 = Choices(choice="Día 2")
        day2.save()
        day3 = Choices(choice="Día 3")
        day3.save()
        day = Questions(question="¿Qué días asistirás?", question_type="checkbox", required=True)
        day.save()
        day.choices.add(day1)
        day.choices.add(day2)
        day.choices.add(day3)
        day.save()
        dietary_none = Choices(choice="Ninguno")
        dietary_none.save()
        dietary_vegetarian = Choices(choice="Vegetariano")
        dietary_vegetarian.save()
        dietary_gluten = Choices(choice="Sin Gluten")
        dietary_gluten.save()
        dietary = Questions(question="Restricción de Dieta", question_type="multiple choice", required=True)
        dietary.save()
        dietary.choices.add(dietary_none)
        dietary.choices.add(dietary_vegetarian)
        dietary.choices.add(dietary_gluten)
        dietary.save()
        accept_agreement = Choices(choice="Yes")
        accept_agreement.save()
        agreement = Questions(question="Entiendo que tendré que pagar $$ al llegar", question_type="checkbox",
                              required=True)
        agreement.save()
        agreement.choices.add(accept_agreement)
        agreement.save()
        form = Form(code=code, title="Registro de Evento", creator=request.user, background_color="#fdefc3",
                    confirmation_message="Hemos recibido su registro.\n\
Inserte otra información aquí.\n\
\n\
Guarde el enlace a continuación, que se puede usar para editar su registro hasta la fecha de cierre de la inscripción..",
                    description="Horario del evento: 4-6 de enero de 2016\n\
Dirección del evento: 123 Tu Calle Tu Ciudad, ST 12345\n\
Contáctanos al (123) 456-7890 o no_reply@example.com", edit_after_submit=True, allow_view_score=False)
        form.save()
        form.questions.add(name)
        form.questions.add(email)
        form.questions.add(organization)
        form.questions.add(day)
        form.questions.add(dietary)
        form.questions.add(agreement)
        form.save()
        return JsonResponse({"message": "Sucess", "code": code})


@login_required(login_url="login")
def delete_responses(request, code):
    formInfo = Form.objects.filter(code=code)
    # Checking if form exists
    if formInfo.count() == 0:
        return HttpResponseRedirect(reverse('404'))
    else:
        formInfo = formInfo[0]
    # Checking if form creator is user
    if not _can_manage_form(request.user, formInfo):
        return HttpResponseRedirect(reverse("403"))
    if request.method == "DELETE":
        responses = Responses.objects.filter(response_to=formInfo)
        for response in responses:
            for i in response.response.all():
                i.delete()
            response.delete()
        return JsonResponse({"message": "Success"})


# Error handler
def FourZeroThree(request):
    return render(request, "error/403.html")


def FourZeroFour(request):
    return render(request, "error/404.html")

