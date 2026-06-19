import os
import secrets
import requests
from flask import Blueprint, redirect, url_for, flash, request
from flask_login import login_user
from models import db, Usuario

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

def init_google_login(app):
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return

    google_bp = Blueprint("google_auth", __name__, url_prefix="/google")

    @google_bp.route("/login")
    def google_login():
        state = secrets.token_urlsafe(32)
        redirect_uri = url_for("google_auth.google_callback", _external=True)
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "prompt": "consent",
        }
        import flask
        flask.session["oauth_state"] = state
        flask.session.permanent = True
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        return redirect(f"{GOOGLE_AUTH_URL}?{qs}")

    @google_bp.route("/callback")
    def google_callback():
        import flask
        error = request.args.get("error")
        if error:
            flash(f"Error de Google: {error}", "danger")
            return redirect(url_for("auth.login"))

        code = request.args.get("code")
        state = request.args.get("state")
        stored_state = flask.session.pop("oauth_state", None)

        if not code or not state or state != stored_state:
            flash("Error de validación OAuth. Intentá de nuevo.", "danger")
            return redirect(url_for("auth.login"))

        redirect_uri = url_for("google_auth.google_callback", _external=True)
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        token_resp = requests.post(GOOGLE_TOKEN_URL, data=token_data)
        if not token_resp.ok:
            flash("Error al obtener token de Google.", "danger")
            return redirect(url_for("auth.login"))

        access_token = token_resp.json()["access_token"]
        user_resp = requests.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
        if not user_resp.ok:
            flash("Error al obtener datos de usuario.", "danger")
            return redirect(url_for("auth.login"))

        info = user_resp.json()
        email = info.get("email", "")
        name = info.get("name", email.split("@")[0])

        user = Usuario.query.filter_by(email=email).first()
        if not user:
            user = Usuario(username=name, email=email)
            user.set_password(secrets.token_hex(16))
            db.session.add(user)
            db.session.commit()

        login_user(user, remember=True)
        return redirect(url_for("main.fixture"))

    app.register_blueprint(google_bp)
