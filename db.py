# db.py

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "sismos.db"

def get_connection():
    """
    Devuelve un objeto sqlite3.Connection conectado a 'sismos.db'.
    """
    conn = sqlite3.connect(DB_PATH)
    # Para que podamos referirnos a columnas por nombre
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Crea las tablas Evento, SerieTemporal, MuestraSismica y CambioEstado si no existen.
    """
    ddl_evento = """
    CREATE TABLE IF NOT EXISTS Evento (
        id_evento       INTEGER PRIMARY KEY,
        fecha_hora      TEXT    NOT NULL,
        epicentro_lat   REAL    NOT NULL,
        epicentro_lng   REAL    NOT NULL,
        hipocentro      REAL    NOT NULL,
        magnitud        REAL    NULL,
        magnitud_desc   TEXT    NULL,
        magnitud_unidad TEXT    NULL,
        alcance_nombre  TEXT    NULL,
        alcance_desc    TEXT    NULL,
        clasif_desde    REAL    NULL,
        clasif_hasta    REAL    NULL,
        clasif_nombre   TEXT    NULL,
        origen_nombre   TEXT    NULL,
        origen_desc     TEXT    NULL,
        estado_nombre   TEXT    NOT NULL,
        estado_desc     TEXT    NULL
    );
    """

    ddl_serie = """
    CREATE TABLE IF NOT EXISTS SerieTemporal (
        id_serie        INTEGER PRIMARY KEY AUTOINCREMENT,
        id_evento       INTEGER NOT NULL,
        estacion        TEXT    NOT NULL,
        fecha_registro  TEXT    NOT NULL,
        FOREIGN KEY (id_evento) REFERENCES Evento(id_evento) ON DELETE CASCADE
    );
    """

    ddl_muestra = """
    CREATE TABLE IF NOT EXISTS MuestraSismica (
        id_muestra      INTEGER PRIMARY KEY AUTOINCREMENT,
        id_serie        INTEGER NOT NULL,
        fecha_muestra   TEXT    NOT NULL,
        velocidad_onda  REAL    NOT NULL,
        frecuencia_onda REAL    NOT NULL,
        longitud_onda   REAL    NOT NULL,
        FOREIGN KEY (id_serie) REFERENCES SerieTemporal(id_serie) ON DELETE CASCADE
    );
    """

    ddl_cambio = """
    CREATE TABLE IF NOT EXISTS CambioEstado (
        id_cambio       INTEGER PRIMARY KEY AUTOINCREMENT,
        id_evento       INTEGER NOT NULL,
        fecha_inicio    TEXT    NOT NULL,
        fecha_fin       TEXT    NULL,
        estado_nombre   TEXT    NOT NULL,
        estado_desc     TEXT    NULL,
        FOREIGN KEY (id_evento) REFERENCES Evento(id_evento) ON DELETE CASCADE
    );
    """

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(ddl_evento)
    cursor.execute(ddl_serie)
    cursor.execute(ddl_muestra)
    cursor.execute(ddl_cambio)
    conn.commit()
    conn.close()

# Al importar db.py, inicializamos las tablas automáticamente
init_db()
