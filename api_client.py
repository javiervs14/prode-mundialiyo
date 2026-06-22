import requests
import os
from datetime import datetime
from config import Config

BASE = Config.API_FOOTBALL_BASE_URL

def _get_headers():
    key = os.environ.get("API_FOOTBALL_KEY", "")
    return {"X-Auth-Token": key}

def _get(endpoint):
    url = f"{BASE}/{endpoint}"
    resp = requests.get(url, headers=_get_headers())
    if resp.status_code == 429:
        raise Exception("Límite de API alcanzado. Esperá 1 minuto.")
    resp.raise_for_status()
    return resp.json()

def get_competition():
    return _get(f"competitions/{Config.WC_COMPETITION_ID}")

def get_teams():
    data = _get(f"competitions/{Config.WC_COMPETITION_ID}/teams")
    return {t["id"]: t["name"] for t in data.get("teams", [])}

def get_matches():
    data = _get(f"competitions/{Config.WC_COMPETITION_ID}/matches")
    return data.get("matches", [])

def parse_matches(matches, teams_dict):
    result = []
    for m in matches:
        if m["status"] == "TIMED":
            goles_l = goles_v = None
            jugado = False
        else:
            score = m.get("score", {})
            full = score.get("fullTime", {}) or score.get("regularTime", {})
            goles_l = full.get("home", 0) if m["status"] == "FINISHED" else None
            goles_v = full.get("away", 0) if m["status"] == "FINISHED" else None
            jugado = m["status"] == "FINISHED"

        home_team = m.get("homeTeam", {}) or {}
        away_team = m.get("awayTeam", {}) or {}

        local = teams_dict.get(home_team.get("id")) or home_team.get("name") or None
        visitante = teams_dict.get(away_team.get("id")) or away_team.get("name") or None

        matchday = m.get("matchday")
        stage = m.get("stage", "GROUP_STAGE")
        group = m.get("group")

        etapa_map = {
            "GROUP_STAGE": "grupos",
            "ROUND_32": "r32",
            "LAST_16": "octavos",
            "QUARTER_FINALS": "cuartos",
            "SEMI_FINALS": "semis",
            "FINAL": "final",
            "THIRD_PLACE": "tercer_puesto"
        }

        etapa = etapa_map.get(stage, stage.lower())

        date_str = m.get("utcDate", "")
        try:
            fecha = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            fecha = datetime.utcnow()

        if etapa == "grupos":
            if not local or not visitante:
                continue
        else:
            local = local or "Por definir"
            visitante = visitante or "Por definir"

        result.append({
            "api_id": m["id"],
            "jornada": matchday,
            "etapa": etapa,
            "grupo": group,
            "local": local,
            "visitante": visitante,
            "goles_local": goles_l,
            "goles_visitante": goles_v,
            "fecha": fecha,
            "jugado": jugado,
        })
    return result
