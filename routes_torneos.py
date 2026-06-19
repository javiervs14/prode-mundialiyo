from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Torneo, Usuario, Prediccion, Partido

torneos_bp = Blueprint("torneos", __name__)

@torneos_bp.route("/torneos")
@login_required
def lista():
    mis_torneos = current_user.torneos
    return render_template("torneos.html", torneos=mis_torneos)

@torneos_bp.route("/torneos/crear", methods=["POST"])
@login_required
def crear():
    nombre = request.form.get("nombre", "").strip()
    if not nombre or len(nombre) < 3:
        flash("El nombre debe tener al menos 3 caracteres.", "danger")
        return redirect(url_for("torneos.lista"))

    torneo = Torneo(nombre=nombre, codigo=Torneo.generar_codigo(), creador_id=current_user.id)
    torneo.participantes.append(current_user)
    db.session.add(torneo)
    db.session.commit()
    flash(f"Torneo '{nombre}' creado. Código: {torneo.codigo}", "success")
    return redirect(url_for("torneos.lista"))

@torneos_bp.route("/torneos/unirse", methods=["POST"])
@login_required
def unirse():
    codigo = request.form.get("codigo", "").strip().upper()
    torneo = Torneo.query.filter_by(codigo=codigo).first()
    if not torneo:
        flash("Código inválido. Verificá que esté bien escrito.", "danger")
        return redirect(url_for("torneos.lista"))

    if current_user in torneo.participantes:
        flash("Ya estás en este torneo.", "warning")
        return redirect(url_for("torneos.lista"))

    torneo.participantes.append(current_user)
    db.session.commit()
    flash(f"Te uniste a '{torneo.nombre}'.", "success")
    return redirect(url_for("torneos.lista"))

@torneos_bp.route("/torneos/<int:torneo_id>")
@login_required
def ver(torneo_id):
    torneo = Torneo.query.get_or_404(torneo_id)
    if current_user not in torneo.participantes:
        flash("No pertenecés a este torneo.", "danger")
        return redirect(url_for("torneos.lista"))

    ranking_data = []
    for u in torneo.participantes:
        pts = torneo.total_puntos_usuario(u.id)
        ranking_data.append({"usuario": u, "puntos": pts})
    ranking_data.sort(key=lambda x: x["puntos"], reverse=True)

    return render_template("torneo.html", torneo=torneo, ranking=ranking_data)

@torneos_bp.route("/torneos/<int:torneo_id>/salir", methods=["POST"])
@login_required
def salir(torneo_id):
    torneo = Torneo.query.get_or_404(torneo_id)
    if current_user not in torneo.participantes:
        flash("No pertenecés a este torneo.", "danger")
        return redirect(url_for("torneos.lista"))

    torneo.participantes.remove(current_user)
    db.session.commit()
    flash(f"Saliste de '{torneo.nombre}'.", "success")
    return redirect(url_for("torneos.lista"))
