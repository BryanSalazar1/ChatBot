"""
Configuración global de pytest.
Mockea MongoDB y las funciones de db para que los tests no necesiten conexión real.
"""
import sys
import os
import pytest

# Agrega src/ al path para que los módulos se importen sin paquete
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture(autouse=True)
def mock_db_functions(monkeypatch):
    """Reemplaza todas las funciones de db por stubs sin I/O."""
    import db

    monkeypatch.setattr(db, "guardar_sesion",         lambda *a, **k: "fake-id")
    monkeypatch.setattr(db, "guardar_turno_memoria",  lambda *a, **k: "fake-id")
    monkeypatch.setattr(db, "obtener_historial",       lambda *a, **k: [])
    monkeypatch.setattr(db, "buscar_contexto_rag",     lambda *a, **k: [])
    monkeypatch.setattr(db, "nueva_sesion_id",         lambda: "test-session-uuid")
