from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user

    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    if not old_password or not new_password:
        return Response(
            {"error": "Ancien et nouveau mot de passe requis"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not user.check_password(old_password):
        return Response(
            {"error": "Ancien mot de passe incorrect"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        validate_password(new_password, user)
    except ValidationError as e:
        return Response(
            {"error": e.messages},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.set_password(new_password)
    user.save()

    # 🔒 Invalidation du token
    Token.objects.filter(user=user).delete()

    return Response(
        {"message": "Mot de passe modifié. Veuillez vous reconnecter."},
        status=status.HTTP_200_OK
    )


##### views.py
# ===== IMPORTS =====
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


# =========================
# PAGE HTML (GET)
# URL : /change-password/
# =========================
@login_required
def change_password_page(request):
    return render(request, "Applications/change_password.html")


# =========================
# API DRF (POST)
# URL : /api/change-password/
# =========================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_api(request):
    user = request.user

    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")

    if not old_password or not new_password:
        return Response(
            {"error": "Tous les champs sont obligatoires"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not user.check_password(old_password):
        return Response(
            {"error": "Ancien mot de passe incorrect"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        validate_password(new_password, user)
    except ValidationError as e:
        return Response(
            {"error": e.messages},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.set_password(new_password)
    user.save()

    # 🔒 Invalidation du token (reconnexion obligatoire)
    Token.objects.filter(user=user).delete()

    return Response(
        {"message": "Mot de passe modifié. Veuillez vous reconnecter."},
        status=status.HTTP_200_OK
    )

urls.py :
from django.urls import path
from .views import change_password_page, change_password_api

app_name = "applications"

urlpatterns = [
    # PAGE HTML
    path("change-password/", change_password_page, name="change_password"),

    # API
    path("api/change-password/", change_password_api, name="api_change_password"),
]

template pour le changement de mdp
{% extends "Applications/base.html" %}

{% block content %}
<div class="container mt-5" style="max-width: 500px;">
    <h3 class="mb-4">Changer le mot de passe</h3>

    <form method="post" action="{% url 'applications:api_change_password' %}">
        {% csrf_token %}

        <div class="mb-3">
            <label class="form-label">Ancien mot de passe</label>
            <input type="password" name="old_password" class="form-control" required>
        </div>

        <div class="mb-3">
            <label class="form-label">Nouveau mot de passe</label>
            <input type="password" name="new_password" class="form-control" required>
        </div>

        <button type="submit" class="btn btn-primary w-100">
            Valider
        </button>
    </form>
</div>
{% endblock %}

tem0lates base.html
<div class="dropdown dropstart">
    <button class="btn btn-secondary dropdown-toggle"
            type="button"
            data-bs-toggle="dropdown">
        <i class="fa-solid fa-gear"></i>
    </button>

    <ul class="dropdown-menu">
        <li>
            <a class="dropdown-item"
               href="{% url 'applications:change_password' %}">
                Changer mot de passe
            </a>
        </li>
        <li>
            <a class="dropdown-item"
               href="{% url 'logout' %}">
                Déconnexion
            </a>
        </li>
    </ul>
</div>

{% extends "Applications/base.html" %}

{% block content %}
<div class="container mt-5" style="max-width: 500px;">
    <h3>Changer le mot de passe</h3>

    <form id="changePasswordForm">
        {% csrf_token %}

        <div class="mb-3">
            <label>Ancien mot de passe</label>
            <input type="password" name="old_password" class="form-control" required>
        </div>

        <div class="mb-3">
            <label>Nouveau mot de passe</label>
            <input type="password" name="new_password" class="form-control" required>
        </div>

        <button class="btn btn-primary w-100">Valider</button>
    </form>
</div>

<script>
document.getElementById("changePasswordForm").addEventListener("submit", function(e) {
    e.preventDefault();

    fetch("{% url 'applications:api_change_password' %}", {
        method: "POST",
        headers: {
            "X-CSRFToken": "{{ csrf_token }}",
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            old_password: this.old_password.value,
            new_password: this.new_password.value
        })
    })
    .then(response => {
        if (response.ok) {
            window.location.href = "{% url 'login' %}";
        } else {
            alert("Erreur lors du changement de mot de passe");
        }
    });
});
</script>
{% endblock %}


{% extends "Applications/base.html" %}

{% block content %}
<div class="container mt-5" style="max-width: 500px;">
    <h3>Créer un compte</h3>

    <form id="registerForm">
        {% csrf_token %}

        <div class="mb-3">
            <label>Nom d'utilisateur</label>
            <input type="text" name="username" class="form-control" required>
        </div>

        <div class="mb-3">
            <label>Email</label>
            <input type="email" name="email" class="form-control">
        </div>

        <div class="mb-3">
            <label>Mot de passe</label>
            <input type="password" name="password" class="form-control" required>
        </div>

        <button class="btn btn-primary w-100">Créer le compte</button>
    </form>

    <div id="error" class="text-danger mt-3"></div>
</div>

<script>
document.getElementById("registerForm").addEventListener("submit", function(e) {
    e.preventDefault();

    fetch("{% url 'applications:api_register' %}", {
        method: "POST",
        headers: {
            "X-CSRFToken": "{{ csrf_token }}",
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            username: this.username.value,
            email: this.email.value,
            password: this.password.value
        })
    })
    .then(response => {
        if (response.ok) {
            window.location.href = "{% url 'login' %}";
        } else {
            return response.json().then(data => {
                document.getElementById("error").innerText =
                    JSON.stringify(data);
            });
        }
    });
});
</script>
{% endblock %}