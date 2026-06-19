import os
import secrets
from flask import Blueprint, redirect, url_for, flash
from flask_login import login_user, current_user
from flask_dance.contrib.google import make_google_blueprint, google
from models import db, Usuario

def init_google_login(app):
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return

    google_bp = make_google_blueprint(
        client_id=client_id,
        client_secret=client_secret,
        scope=["openid", "email", "profile"],
        redirect_to="google_authorized",
    )
    app.register_blueprint(google_bp, url_prefix="/login/google")

    @app.route("/login/google/done")
    def google_authorized():
        if not google.authorized:
            return redirect(url_for("auth.login"))

        resp = google.get("/oauth2/v2/userinfo")
        if not resp.ok:
            flash("Error al conectar con Google.", "danger")
            return redirect(url_for("auth.login"))

        info = resp.json()
        email = info.get("email", "")
        name = info.get("name", email.split("@")[0])

        user = Usuario.query.filter_by(email=email).first()
        if not user:
            user = Usuario(username=name, email=email)
            user.set_password(secrets.token_hex(16))
            db.session.add(user)
            db.session.commit()

        login_user(user)
        return redirect(url_for("main.fixture"))
