from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from models import db, Usuario

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("Todos los campos son obligatorios.", "danger")
            return render_template("registro.html")

        if Usuario.query.filter_by(username=username).first():
            flash("El usuario ya existe.", "danger")
            return render_template("registro.html")

        if Usuario.query.filter_by(email=email).first():
            flash("El email ya está registrado.", "danger")
            return render_template("registro.html")

        user = Usuario(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Registro exitoso. Ahora podés iniciar sesión.", "success")
        return redirect(url_for("auth.login"))
    return render_template("registro.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = Usuario.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash("Usuario o contraseña incorrectos.", "danger")
            return render_template("login.html")

        login_user(user, remember=True)
        return redirect(url_for("main.fixture"))
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
