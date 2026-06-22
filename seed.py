from models import db, Partido, Prediccion
from api_client import get_matches, get_teams, parse_matches

def seed_data():
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
        print("No se cargaron datos. Usá /admin/reset para reintentar.")

def _seed_fallback():
    equipos_base = [
        ("Argentina", "Brasil", "Uruguay", "Colombia"),
        ("Francia", "España", "Inglaterra", "Alemania"),
        ("Italia", "Países Bajos", "Portugal", "Bélgica"),
        ("México", "EE.UU.", "Canadá", "Costa Rica"),
        ("Japón", "Corea del Sur", "Arabia Saudita", "Australia"),
        ("Marruecos", "Senegal", "Nigeria", "Camerún"),
    ]

    from datetime import datetime
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
    import requests

    try:
        teams = get_teams()
        matches = get_matches()
        parsed = parse_matches(matches, teams)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión con la API: {e}")
        return

    actualizados = 0
    equipos_actualizados = 0
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
            db.session.commit()

        if p.etapa != "grupos":
            if p.local == "Por definir" and m["local"] != "Por definir":
                p.local = m["local"]
                equipos_actualizados += 1
            if p.visitante == "Por definir" and m["visitante"] != "Por definir":
                p.visitante = m["visitante"]
                equipos_actualizados += 1

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

    db.session.commit()
    if actualizados:
        print(f"Se actualizaron {actualizados} resultados.")
    if equipos_actualizados:
        print(f"Se actualizaron {equipos_actualizados} equipos en eliminatorias.")
    if not actualizados and not equipos_actualizados:
        print("No hay novedades.")

def force_seed():
    Prediccion.query.delete()
    Partido.query.delete()
    db.session.commit()

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
        return True, f"Se cargaron {len(parsed)} partidos reales."
    except Exception as e:
        db.session.rollback()
        return False, f"Error al conectar con la API: {e}"
