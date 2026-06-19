import os
import sys
from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, Usuario, Partido, Prediccion
from routes_auth import auth_bp
from routes_main import main_bp
from apscheduler.schedulers.background import BackgroundScheduler
from flags import PAISES_BANDERAS
from routes_google import init_google_login
from flask_session import Session

app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
Session(app)

@app.context_processor
def inject_globals():
    def flag_url(pais):
        code = PAISES_BANDERAS.get(pais, "")
        if not code:
            return ""
        return f"https://flagcdn.com/24x18/{code}.png"
    return dict(flag_url=flag_url)

app.config.from_object(Config)
app.config["SQLALCHEMY_DATABASE_URI"] = Config.SQLALCHEMY_DATABASE_URI

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Iniciá sesión para acceder."
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))

app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
init_google_login(app)

scheduler = BackgroundScheduler()
scheduler_started = False

def auto_update():
    global scheduler_started
    if not scheduler_started:
        return
    with app.app_context():
        actualizar_resultados()

def seed_data():
    from api_client import get_matches, get_teams, parse_matches

    if Partido.query.first():
        return

    print("Cargando datos desde football-data.org...")
    try:
        teams = get_teams()
        matches = get_matches()
        parsed = parse_matches(matches, teams)

        for m in parsed:
            p = Partido(
                api_id=m["api_id"],
                jornada=m["jornada"],
                etapa=m["etapa"],
                grupo=m["grupo"],
                local=m["local"],
                visitante=m["visitante"],
                goles_local=m["goles_local"],
                goles_visitante=m["goles_visitante"],
                fecha=m["fecha"],
                jugado=m["jugado"],
                actualizado=m["jugado"],
            )
            db.session.add(p)

        db.session.commit()

        partidos_jugados = Partido.query.filter_by(jugado=True).all()
        for p in partidos_jugados:
            preds = Prediccion.query.filter_by(partido_id=p.id).all()
            for pred in preds:
                pred.calcular_puntos()
        db.session.commit()

        print(f"Se cargaron {len(parsed)} partidos.")
    except Exception as e:
        print(f"Error al conectar con la API: {e}")
        print("Cargando datos de respaldo...")
        _seed_fallback()

def _seed_fallback():
    equipos_base = [
        ("Argentina", "Brasil", "Uruguay", "Colombia"),
        ("Francia", "España", "Inglaterra", "Alemania"),
        ("Italia", "Países Bajos", "Portugal", "Bélgica"),
        ("México", "EE.UU.", "Canadá", "Costa Rica"),
        ("Japón", "Corea del Sur", "Arabia Saudita", "Australia"),
        ("Marruecos", "Senegal", "Nigeria", "Camerún"),
    ]

    from datetime import datetime, timedelta
    for gi, grupo in enumerate(equipos_base, 1):
        for i in range(4):
            for j in range(i + 1, 4):
                day = min(12 + gi * 3 + i + j, 30)
                p = Partido(
                    api_id=-(gi * 100 + i * 10 + j),
                    jornada=1,
                    etapa="grupos",
                    grupo=f"Grupo {chr(64 + gi)}",
                    local=grupo[i],
                    visitante=grupo[j],
                    goles_local=None,
                    goles_visitante=None,
                    fecha=datetime(2026, 6, day),
                    jugado=False,
                )
                db.session.add(p)
    db.session.commit()
    print(f"Datos de respaldo cargados ({len(equipos_base) * 6} partidos de grupos).")

def actualizar_resultados():
    from api_client import get_matches, get_teams, parse_matches
    import requests

    try:
        teams = get_teams()
        matches = get_matches()
        parsed = parse_matches(matches, teams)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión con la API: {e}")
        return

    actualizados = 0
    for m in parsed:
        p = Partido.query.filter_by(api_id=m["api_id"]).first()
        if not p:
            p = Partido(
                api_id=m["api_id"],
                jornada=m["jornada"],
                etapa=m["etapa"],
                grupo=m["grupo"],
                local=m["local"],
                visitante=m["visitante"],
                fecha=m["fecha"],
            )
            db.session.add(p)

        if m["jugado"] and m["goles_local"] is not None and (not p.actualizado):
            p.goles_local = m["goles_local"]
            p.goles_visitante = m["goles_visitante"]
            p.jugado = True
            p.actualizado = True
            actualizados += 1

            preds = Prediccion.query.filter_by(partido_id=p.id).all()
            for pred in preds:
                pred.calcular_puntos()
            db.session.commit()

    if actualizados:
        db.session.commit()
        print(f"Se actualizaron {actualizados} resultados.")
    else:
        print("No hay resultados nuevos.")

def start_scheduler():
    global scheduler_started
    if scheduler_started:
        return
    scheduler.add_job(auto_update, "interval", hours=1, id="actualizar_resultados", replace_existing=True)
    scheduler.start()
    scheduler_started = True
    print("Actualizador automático iniciado (cada 1 hora).")

def init_db():
    with app.app_context():
        db.create_all()
        if os.environ.get("RENDER"):
            if Partido.query.count() == 0:
                seed_data()
            start_scheduler()

init_db()

if __name__ == "__main__":
    if "--seed" in sys.argv:
        with app.app_context():
            seed_data()
    if "--update" in sys.argv:
        with app.app_context():
            actualizar_resultados()
    if not any(arg in sys.argv for arg in ["--seed", "--update"]):
        app.run(debug=True)
