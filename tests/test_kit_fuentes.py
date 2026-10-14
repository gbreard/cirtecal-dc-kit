"""Fuentes: interfaz y reglas de consulta (sin red)."""
import pytest

from kit.fuentes import aduana_plantilla, http, peeringdb


def test_plantilla_exige_implementacion():
    with pytest.raises(NotImplementedError):
        list(aduana_plantilla.FuenteAduana().importaciones(["x"], [2020]))


def test_archivo_csv(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("anio,codigo,origen,valor_usd,kg\n2020,A,China,10,\n2021,B,,5,1\n",
                 encoding="utf-8")
    regs = list(aduana_plantilla.ArchivoCSV(str(p)).importaciones(["A"], None))
    assert len(regs) == 1 and regs[0].kg is None and regs[0].origen == "China"


def test_peeringdb_pausa_minima(monkeypatch):
    assert peeringdb.PAUSA_S >= 2.0


def test_user_agent_sin_correo():
    assert "@" not in http.USER_AGENT


def test_403_no_se_fuerza(monkeypatch):
    class R:
        status_code, ok, text = 403, False, ""
    import requests
    monkeypatch.setattr(requests, "get", lambda *a, **k: R())
    with pytest.raises(http.Bloqueado):
        http.get("https://ejemplo.invalid/x", 0)
