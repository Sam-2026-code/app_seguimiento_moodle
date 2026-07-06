import requests
import unicodedata
from datetime import datetime, timezone
import pandas as pd


class MoodleClient:
    def __init__(self, url: str, token: str):
        self.url = url.rstrip("/")
        self.token = token
        self.format = "json"

    def _call(self, wsfunction: str, params: dict = None, method: str = "post", timeout: int = 30):
        if params is None:
            params = {}
        url = f"{self.url}/webservice/rest/server.php"
        payload = {
            "wstoken": self.token,
            "wsfunction": wsfunction,
            "moodlewsrestformat": self.format,
            **params,
        }
        try:
            if method.lower() == "get":
                r = requests.get(url, params=payload, timeout=timeout)
            else:
                r = requests.post(url, data=payload, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise RuntimeError(f"Error calling Moodle ({wsfunction}): {e}")

    @staticmethod
    def _epoch_to_str(ts):
        try:
            return datetime.fromtimestamp(int(ts), tz=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

    @staticmethod
    def _clean_text(s):
        if not isinstance(s, str):
            return ""
        s = s.strip()
        s = unicodedata.normalize("NFKD", s)
        return "".join(c for c in s if not unicodedata.combining(c))

    def find_user_by_dni(self, dni: str):
        if not dni:
            return []
        try:
            res = self._call("core_user_get_users_by_field", {"field": "username", "values[0]": str(dni)})
            if isinstance(res, list) and res:
                return res
        except RuntimeError:
            pass
        try:
            res = self._call("core_user_get_users_by_field", {"field": "idnumber", "values[0]": str(dni)})
            if isinstance(res, list):
                return res
        except RuntimeError:
            pass
        return []

    def find_user_by_name(self, firstname: str, lastname: str):
        q = f"{firstname} {lastname}".strip()
        if not q:
            return []
        try:
            res = self._call("core_user_get_users", {"criteria[0][key]": "query", "criteria[0][value]": q})
            if isinstance(res, dict) and res.get("users"):
                return res["users"]
            if isinstance(res, list):
                return res
        except RuntimeError:
            pass
        return []

    def get_user_courses(self, userid: int):
        try:
            res = self._call("core_enrol_get_users_courses", {"userid": userid})
            if isinstance(res, list):
                return res
        except RuntimeError:
            pass
        return []

    def _get_course_sections(self, courseid: int):
        try:
            res = self._call("core_course_get_contents", {"courseid": courseid})
            sections = {}
            if isinstance(res, list):
                for sec in res:
                    sec_name = sec.get("name") or f"Sección {sec.get('section', 'N/A')}"
                    for mod in sec.get("modules", []):
                        mod_id = mod.get("id")
                        if mod_id:
                            sections[mod_id] = sec_name
            return sections
        except RuntimeError:
            return {}

    def _get_course_lastaccess(self, courseid: int, userid: int):
        try:
            res = self._call("core_user_get_course_user_profiles", {"courseid": courseid, "userid": userid})
            if isinstance(res, list) and len(res) > 0:
                item = res[0]
                for k in ("lastaccess", "lastlogin", "timeaccess"):
                    if k in item and item.get(k):
                        return self._epoch_to_str(item.get(k))
        except RuntimeError:
            pass
        return None

    def get_course_progress(self, courseid: int, userid: int):
        completed_count = 0
        total_activities = 0
        last_name = "Sin actividad"
        last_ts = 0
        sections_map = self._get_course_sections(courseid)

        try:
            res = self._call("core_completion_get_activities_completion_status", {"courseid": courseid, "userid": userid})
            activities = res.get("activities") or res.get("statuses") or []
            total_activities = len(activities)
            for a in activities:
                state = a.get("completionstate") or a.get("state")
                try:
                    if state is not None and int(state) in (1, 2):
                        completed_count += 1
                except (ValueError, TypeError):
                    pass
                ts_candidates = [int(a.get(k, 0)) for k in ("timemodified", "timecompleted", "completiontime") if a.get(k)]
                ts = max(ts_candidates) if ts_candidates else 0
                if ts and ts > last_ts:
                    last_ts = ts
                    mod_name = a.get("name") or "Actividad"
                    sec_name = sections_map.get(a.get("cmid"), "Sin sección")
                    last_name = f"{sec_name} > {mod_name}"
        except RuntimeError:
            pass

        pct = round(completed_count / total_activities, 2) if total_activities > 0 else 0
        last_time_str = self._epoch_to_str(last_ts) if last_ts > 0 else "Aún no comenzó"
        return pct, last_name, last_time_str

    def process_csv(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [self._clean_text(c) for c in df.columns]
        col_nombre, col_apellido, col_dni = "nombre", "apellido", "dni"

        total_rows = len(df)
        yield {"tipo": "inicio", "total": total_rows}

        out_rows = []

        for idx, row in df.iterrows():
            val_nombre = (row.get(col_nombre) or "").strip()
            val_apellido = (row.get(col_apellido) or "").strip()
            val_dni = str(row.get(col_dni) or "").strip()

            if not val_nombre and not val_apellido and not val_dni:
                continue

            yield {"tipo": "status", "mensaje": f"Analizando: {val_nombre} {val_apellido}", "fila": idx}

            found_users = []
            if val_dni:
                found_users = self.find_user_by_dni(val_dni)
            if not found_users:
                found_users = self.find_user_by_name(val_nombre, val_apellido)

            if not found_users:
                out_rows.append({
                    "DNI": val_dni,
                    "Nombre y apellido": f"{val_nombre} {val_apellido}",
                    "Curso": "",
                    "Porcentaje Progreso": 0,
                    "Ultimo módulo visto": "",
                    "Fecha último módulo": "No encontrado en Moodle",
                })
                continue

            for u in found_users:
                userid = u.get("id")
                fullname = f"{u.get('firstname', '')} {u.get('lastname', '')}".strip()
                courses = self.get_user_courses(userid)

                if not courses:
                    out_rows.append({
                        "DNI": val_dni,
                        "Nombre y apellido": fullname,
                        "Curso": "",
                        "Porcentaje Progreso": 0,
                        "Ultimo módulo visto": "",
                        "Fecha último módulo": "Sin cursos asignados",
                    })
                    continue

                for c in courses:
                    cid = c.get("id")
                    cname = c.get("fullname", "Curso sin nombre")
                    last_access = self._get_course_lastaccess(cid, userid)
                    pct, last_mod, last_date = self.get_course_progress(cid, userid)

                    fecha_final = last_date if last_date and last_date != "Sin registro" else (last_access if last_access else "Aún no comenzó")
                    if last_date == "Aún no comenzó" and last_access:
                        last_mod = "Entró al curso pero no completó actividades"

                    out_rows.append({
                        "DNI": val_dni,
                        "Nombre y apellido": fullname,
                        "Curso": cname,
                        "Porcentaje Progreso": pct,
                        "Ultimo módulo visto": last_mod,
                        "Fecha último módulo": fecha_final,
                    })

                    yield {"tipo": "progreso", "curso": cname, "pct": pct}

        yield {"tipo": "completo", "rows": out_rows}
