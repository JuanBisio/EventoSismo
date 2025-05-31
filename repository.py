import sqlite3
from db import get_connection
from indexClases import (
    Estado, CambioEstado, EventoSismico,
    UbicacionEvento, MuestraSismica, SerieTemporal,
    ClasificacionSismo, OrigenDeGeneracion, AnalistaEnSismos
)
from datetime import datetime

# ---------------------------------------
# FUNCIONES PARA EVENTO
# ---------------------------------------

def guardar_evento(evento: EventoSismico):
    """
    Inserta o actualiza un EventoSismico en la tabla Evento.
    - Si id_evento existe, hace UPDATE.
    - Si no existe, hace INSERT.
    También guarda el estado actual proveniente de evento.estado.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Primero verificamos si ya existe un registro con ese id_evento
    cursor.execute("SELECT 1 FROM Evento WHERE id_evento = ?", (evento.id_evento,))
    existe = cursor.fetchone() is not None

    # Extraemos ubicación:
    lat = evento.ubicacion.getLatitudEpicentro()
    lng = evento.ubicacion.getLongitudEpicentro()
    hip = evento.ubicacion.getHipocentro()

    # Extraemos magnitud (puede ser None o str; convertimos a float si es posible)
    try:
        mag_num = float(evento.magnitud)
        mag_desc = evento.magnitud.descripcion if hasattr(evento.magnitud, "descripcion") else None
        mag_unit = evento.magnitud.unidad if hasattr(evento.magnitud, "unidad") else None
    except Exception:
        # Asumiremos que magnitud es un string que no convertible a float, o None
        mag_num = None
        mag_desc = None
        mag_unit = None

    # Extraemos alcance
    alc_nombre = evento.alcance.getNombre() if evento.alcance else None
    alc_desc   = evento.alcance.descripcion if evento.alcance and hasattr(evento.alcance, "descripcion") else None

    # Extraemos clasificación
    if evento.clasificacion:
        clas_desde = evento.clasificacion.km_profundidad_desde
        clas_hasta = evento.clasificacion.km_profundidad_hasta
        clas_nombre= evento.clasificacion.getNombre()
    else:
        clas_desde = None
        clas_hasta = None
        clas_nombre= None

    # Extraemos origen
    ori_nombre = evento.origen.getNombre() if evento.origen else None
    ori_desc   = evento.origen.descripcion if evento.origen and hasattr(evento.origen, "descripcion") else None

    # Extraemos estado actual
    est_nombre = evento.estado.getNombre()
    est_desc   = evento.estado.getDescripcion()

    if existe:
        # UPDATE
        sql_update = """
        UPDATE Evento SET
            fecha_hora      = ?,
            epicentro_lat   = ?, epicentro_lng = ?, hipocentro = ?,
            magnitud        = ?, magnitud_desc   = ?, magnitud_unidad = ?,
            alcance_nombre  = ?, alcance_desc    = ?,
            clasif_desde    = ?, clasif_hasta    = ?, clasif_nombre = ?,
            origen_nombre   = ?, origen_desc     = ?,
            estado_nombre   = ?, estado_desc     = ?
        WHERE id_evento = ?;
        """
        cursor.execute(sql_update, (
            evento.fecha_hora,
            lat, lng, hip,
            mag_num, mag_desc, mag_unit,
            alc_nombre, alc_desc,
            clas_desde, clas_hasta, clas_nombre,
            ori_nombre, ori_desc,
            est_nombre, est_desc,
            evento.id_evento
        ))
    else:
        # INSERT
        sql_insert = """
        INSERT INTO Evento (
            id_evento, fecha_hora,
            epicentro_lat, epicentro_lng, hipocentro,
            magnitud, magnitud_desc, magnitud_unidad,
            alcance_nombre, alcance_desc,
            clasif_desde, clasif_hasta, clasif_nombre,
            origen_nombre, origen_desc,
            estado_nombre, estado_desc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        cursor.execute(sql_insert, (
            evento.id_evento,
            evento.fecha_hora,
            lat, lng, hip,
            mag_num, mag_desc, mag_unit,
            alc_nombre, alc_desc,
            clas_desde, clas_hasta, clas_nombre,
            ori_nombre, ori_desc,
            est_nombre, est_desc
        ))

    conn.commit()
    conn.close()

def cargar_evento_por_id(id_evento) -> EventoSismico | None:
    """
    Lee la fila de Evento con id=id_evento, lee también sus Cambios de estado,
    y reconstruye un objeto EventoSismico con su historial completo.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Consultamos la tabla Evento
    cursor.execute("SELECT * FROM Evento WHERE id_evento = ?", (id_evento,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    # Reconstruimos los campos necesarios
    fecha_hora = row["fecha_hora"]
    epic_lat   = row["epicentro_lat"]
    epic_lng   = row["epicentro_lng"]
    hipocentro = row["hipocentro"]

    # Crear UbicacionEvento
    ubic = UbicacionEvento((epic_lat, epic_lng), hipocentro)

    # Magnitud: intentamos reconstruir MagnitudRichter si la info existe
    if row["magnitud"] is not None:
        mag_num  = row["magnitud"]
        mag_desc = row["magnitud_desc"]
        mag_unit = row["magnitud_unidad"]
        from indexClases import MagnitudRichter
        mag_obj = MagnitudRichter(mag_num, mag_desc or "", mag_unit or "")
    else:
        mag_obj = None

    # Alcance
    if row["alcance_nombre"] is not None:
        alc_obj = None
        from indexClases import AlcanceSismo
        alc_obj = AlcanceSismo(row["alcance_desc"] or "", row["alcance_nombre"])
    else:
        alc_obj = None

    # Clasificación
    if row["clasif_desde"] is not None:
        clas_obj = ClasificacionSismo(row["clasif_desde"], row["clasif_hasta"], row["clasif_nombre"])
    else:
        clas_obj = None

    # Origen
    if row["origen_nombre"] is not None:
        ori_obj = OrigenDeGeneracion(row["origen_nombre"], row["origen_desc"] or "")
    else:
        ori_obj = None

    # Creamos el objeto EventoSismico
    evento = EventoSismico(
        row["id_evento"],
        fecha_hora,
        ubic,
        mag_obj,
        alc_obj,
        clas_obj,
        ori_obj
    )

    # Ahora reconstruimos el estado actual (sobreescribimos el estado auto-detectado que trae por defecto)
    estado_actual = Estado(row["estado_nombre"], row["estado_desc"] or "")
    evento.estado = estado_actual

    # -------------- CARGAR HISTORIAL DE CAMBIOS ------------------
    cursor.execute("""
        SELECT * FROM CambioEstado
        WHERE id_evento = ?
        ORDER BY fecha_inicio ASC
    """, (id_evento,))
    filas = cursor.fetchall()

    for fila in filas:
        est = Estado(fila["estado_nombre"], fila["estado_desc"] or "")
        cambio = CambioEstado(
            fila["fecha_inicio"],
            est,
            fila["fecha_fin"]
        )
        evento.cambios.append(cambio)

    conn.close()
    return evento

# ---------------------------------------
# FUNCIONES PARA CAMBIO DE ESTADO
# ---------------------------------------

def guardar_cambio_estado(id_evento: int, cambio: CambioEstado):
    """
    Inserta un nuevo registro en la tabla CambioEstado para el evento dado.
    Se asume que la fila de Evento ya existe (o se guardó antes).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO CambioEstado (
            id_evento,
            fecha_inicio,
            fecha_fin,
            estado_nombre,
            estado_desc
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        id_evento,
        cambio.fecha_hora_inicio,
        cambio.fecha_hora_fin,
        cambio.estado.getNombre(),
        cambio.estado.getDescripcion()
    ))
    conn.commit()
    conn.close()

def actualizar_fecha_fin_ultimo_cambio(id_evento: int, fecha_fin: str):
    """
    Actualiza la fecha_fin del último cambio (el que no tiene fecha_fin aún)
    para el evento id_evento.
    """
    conn = get_connection()
    cursor = conn.cursor()
    # Localizar el cambio con fecha_fin NULL y el mayor fecha_inicio
    cursor.execute("""
        UPDATE CambioEstado
        SET fecha_fin = ?
        WHERE id_evento = ? AND fecha_fin IS NULL
    """, (fecha_fin, id_evento))
    conn.commit()
    conn.close()
