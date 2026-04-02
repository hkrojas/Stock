import httpx
from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.blueprints.auth import auth_bp
from app.models import User
from app.utils.api_client import APIClient


@auth_bp.route("/login", methods=["GET", "POST"])
async def login():
    """Show login form and authenticate against FastAPI."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        remember = request.form.get("remember") == "on"

        if not username or not password:
            flash("Por favor ingresa tu usuario y contraseña.", "error")
            return render_template("auth/login.html")

        try:
            token_data = await APIClient(token=None).post(
                "/auth/login",
                data={"username": username, "password": password},
            )
            access_token = token_data.get("access_token")
            if not access_token:
                flash("La API no devolvió un token de acceso válido.", "error")
                return render_template("auth/login.html")

            session["access_token"] = access_token
            session.pop("user_data", None)  # Clear cache to fetch fresh data
            user_data = await APIClient(token=access_token).get("/auth/me")
            session["user_data"] = user_data # Cache it
            user = User(user_data)
            login_user(user, remember=remember)

            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))
        except httpx.HTTPStatusError as exc:
            detail = APIClient.error_detail(exc)
            if exc.response is not None and exc.response.status_code == 401:
                flash("Usuario o contraseña incorrectos.", "error")
            else:
                flash(f"Error de autenticación: {detail}", "error")
        except httpx.RequestError:
            flash("Error de conexión con el servidor de autenticación.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Log the current user out."""
    session.pop("access_token", None)
    session.pop("user_data", None)
    session.pop("view_as_admin", None)
    logout_user()
    flash("Has cerrado sesión correctamente.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/toggle_role")
@login_required
def toggle_role():
    """Toggle superadmin to view the application as a regular admin."""
    if current_user.role == "superadmin":
        if session.get("view_as_admin"):
            session.pop("view_as_admin", None)
            flash("Has regresado a la vista completa de Superadmin.", "info")
        else:
            session["view_as_admin"] = True
            flash("Modo prueba activado. Estás viendo la plataforma como Administrador de Edificio.", "info")
    return redirect(url_for("dashboard.index"))
