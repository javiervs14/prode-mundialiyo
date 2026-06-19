from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    predicciones = db.relationship("Prediccion", backref="usuario", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def total_puntos(self):
        return db.session.query(db.func.coalesce(db.func.sum(Prediccion.puntos), 0)).join(
            Partido, Prediccion.partido_id == Partido.id
        ).filter(
            Prediccion.usuario_id == self.id,
            Prediccion.puntos.isnot(None),
            Partido.jornada >= 3
        ).scalar()

class Partido(db.Model):
    __tablename__ = "partidos"
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.Integer, unique=True, nullable=False)
    jornada = db.Column(db.Integer, nullable=True)
    etapa = db.Column(db.String(50), nullable=False, default="grupos")
    grupo = db.Column(db.String(10), nullable=True)
    local = db.Column(db.String(100), nullable=False)
    visitante = db.Column(db.String(100), nullable=False)
    goles_local = db.Column(db.Integer, nullable=True)
    goles_visitante = db.Column(db.Integer, nullable=True)
    fecha = db.Column(db.DateTime, nullable=False)
    jugado = db.Column(db.Boolean, default=False)
    actualizado = db.Column(db.Boolean, default=False)
    predicciones = db.relationship("Prediccion", backref="partido", lazy="dynamic")

class Prediccion(db.Model):
    __tablename__ = "predicciones"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    partido_id = db.Column(db.Integer, db.ForeignKey("partidos.id"), nullable=False)
    goles_local = db.Column(db.Integer, nullable=False)
    goles_visitante = db.Column(db.Integer, nullable=False)
    puntos = db.Column(db.Integer, nullable=True)
    bloqueado = db.Column(db.Boolean, default=False)
    creada = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("usuario_id", "partido_id", name="uq_usuario_partido"),)

    def calcular_puntos(self):
        p = self.partido
        if p.goles_local is None or p.goles_visitante is None:
            self.puntos = None
            return
        if self.goles_local == p.goles_local and self.goles_visitante == p.goles_visitante:
            self.puntos = 3
        else:
            res_real = "L" if p.goles_local > p.goles_visitante else ("V" if p.goles_visitante > p.goles_local else "E")
            res_pred = "L" if self.goles_local > self.goles_visitante else ("V" if self.goles_visitante > self.goles_local else "E")
            self.puntos = 1 if res_real == res_pred else 0
