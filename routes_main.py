from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Partido, Prediccion, Usuario
from sqlalchemy import case
import os

main_bp = Blueprint("main", __name__)

def _orden_etapa(etapa):
    orden = {
        "grupos": 0,
        "dieciseisavos": 1,
        "octavos": 2,
        "cuartos": 3,
        "semis": 4,
        "tercer_puesto": 5,
        "final": 6,
    }
    return orden.get(etapa, 99)

@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.fixture"))
    return render_template("index.html")

@main_bp.route("/fixture")
@login_required
def fixture():
    partidos = Partido.query.order_by(Partido.fecha).all()
    partidos.sort(key=lambda p: (_orden_etapa(p.etapa), p.jornada or 0, p.fecha))
    return render_template("fixture.html", partidos=partidos)

@main_bp.route("/predicciones", methods=["GET", "POST"])
@login_required
def predicciones():
    if request.method == "POST":
        for key, value in request.form.items():
            if key.startswith("local_"):
                partido_id = int(key.split("_")[1])
                goles_local = request.form.get(f"local_{partido_id}", type=int)
                goles_visitante = request.form.get(f"visit_{partido_id}", type=int)
                if goles_local is None or goles_visitante is None:
                    continue
                partido = Partido.query.get(partido_id)
                if not partido or partido.jugado:
                    continue
                pred = Prediccion.query.filter_by(
                    usuario_id=current_user.id, partido_id=partido_id
                ).first()
                if pred and pred.bloqueado:
                    continue
                if pred:
                    pred.goles_local = goles_local
                    pred.goles_visitante = goles_visitante
                    pred.bloqueado = True
                else:
                    pred = Prediccion(
                        usuario_id=current_user.id,
                        partido_id=partido_id,
                        goles_local=goles_local,
                        goles_visitante=goles_visitante,
                        bloqueado=True,
                    )
                    db.session.add(pred)
        db.session.commit()
        flash("Predicciones guardadas.", "success")
        return redirect(url_for("main.predicciones"))

    partidos = Partido.query.filter(
        Partido.jornada >= 3,
        Partido.local != "Por definir",
        Partido.visitante != "Por definir"
    ).order_by(Partido.fecha).all()
    partidos.sort(key=lambda p: (_orden_etapa(p.etapa), p.jornada or 0, p.fecha))

    predicciones_user = {
        p.partido_id: p
        for p in Prediccion.query.filter_by(usuario_id=current_user.id).all()
    }

    ya_jugados_todos = Partido.query.filter(Partido.jornada >= 3, Partido.jugado == False).count() == 0

    return render_template(
        "predicciones.html",
        partidos=partidos,
        preds=predicciones_user,
        ya_jugados_todos=ya_jugados_todos,
    )

@main_bp.route("/ranking")
@login_required
def ranking():
    usuarios = Usuario.query.all()
    ranking_data = []
    for u in usuarios:
        pts = u.total_puntos()
        ranking_data.append({"usuario": u, "puntos": pts})
    ranking_data.sort(key=lambda x: x["puntos"], reverse=True)
    return render_template("ranking.html", ranking=ranking_data)

@main_bp.route("/admin/reset")
@login_required
def admin_reset():
    secret = request.args.get("secret", "")
    if secret != os.environ.get("ADMIN_SECRET", "MUNDIALIYO2026"):
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("main.fixture"))

    try:
        Prediccion.query.delete()
        Partido.query.delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Error al limpiar datos: {e}", "danger")
        return redirect(url_for("main.fixture"))

    from seed import force_seed
    ok, msg = force_seed()
    if ok:
        flash(msg, "success")
    else:
        flash(f"Error al recargar: {msg}", "danger")

    return redirect(url_for("main.fixture"))

@main_bp.route("/admin/update")
@login_required
def admin_update():
    from seed import actualizar_resultados
    try:
        with db.session.begin():
            actualizar_resultados()
        flash("Resultados actualizados desde la API.", "success")
    except Exception as e:
        flash(f"Error al actualizar: {e}", "danger")
    return redirect(url_for("main.fixture"))

@main_bp.route("/admin/status")
@login_required
def admin_status():
    import os
    key = os.environ.get("API_FOOTBALL_KEY", "")
    has_key = bool(key)
    key_preview = key[:6] + "..." if len(key) > 6 else "(vacía)"
    total = Partido.query.count()
    jugados = Partido.query.filter_by(jugado=True).count()
    db_url = os.environ.get("DATABASE_URL", "")[:40]
    return render_template("admin_status.html", has_key=has_key, key_preview=key_preview, total=total, jugados=jugados, db_url=db_url)
