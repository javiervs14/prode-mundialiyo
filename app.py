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
from seed import seed_data, actualizar_resultados

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
