import sqlite3
from indexClases import (
    EventoSismico,
    UbicacionEvento,
    AlcanceSismo,
    ClasificacionSismo,
    OrigenDeGeneracion,
    Estado,
    CambioEstado,     
    SerieTemporal,
    MuestraSismica
)
from db import get_connection

# ------------ Guardar un Evento (incluye series y muestras) ------------

def guardar_evento(evento: EventoSismico):
    conn = get_connection()
    c = conn.cursor()

    # 1) Insertar o reemplazar la fila base en Evento
    c.execute("""
        INSERT OR REPLACE INTO Evento (
            id_evento,
            fecha_hora,
            epicentro_lat,
            epicentro_lng,
            hipocentro,
            magnitud,
            magnitud_desc,
            magnitud_unidad,
            alcance_nombre,
            alcance_desc,
            clasif_desde,
            clasif_hasta,
            clasif_nombre,
            origen_nombre,
            origen_desc,
            estado_nombre,
            estado_desc
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        evento.id_evento,
        evento.fecha_hora,
        evento.ubicacion.epicentro[0],
        evento.ubicacion.epicentro[1],
        evento.ubicacion.hipocentro,
        float(evento.magnitud) if evento.magnitud else None,
        None,
        None,
        evento.alcance.nombre,
        evento.alcance.descripcion,
        evento.clasificacion.km_profundidad_desde,
        evento.clasificacion.km_profundidad_hasta,
        evento.clasificacion.nombre,
        evento.origen.nombre,
        evento.origen.descripcion,
        evento.estado.nombre,
        evento.estado.descripcion
    ))

    # 2) Eliminar series temporales antiguas para este evento
    c.execute("DELETE FROM SerieTemporal WHERE id_evento = ?", (evento.id_evento,))

    # 3) Insertar cada serie y sus muestras
    for serie in evento.series_temporales:
        c.execute("""
            INSERT INTO SerieTemporal (
                id_evento,
                estacion,
                fecha_registro
            ) VALUES (?,?,?)
        """, (
            evento.id_evento,
            serie.condicion_alarma,
            serie.fecha_hora_registro
        ))
        id_serie = c.lastrowid
        for muestra in serie.muestras:
            c.execute("""
                INSERT INTO MuestraSismica (
                    id_serie,
                    fecha_muestra,
                    velocidad_onda,
                    frecuencia_onda,
                    longitud_onda
                ) VALUES (?,?,?,?,?)
            """, (
                id_serie,
                muestra.fecha_hora_muestra,
                muestra.velocidad_onda,
                muestra.frecuencia_onda,
                muestra.longitud_onda
            ))

    conn.commit()
    conn.close()

# ------------ Guardar un Cambio de Estado ------------

def guardar_cambio_estado(event_id: int, cambio: CambioEstado):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO CambioEstado (
            id_evento,
            fecha_inicio,
            fecha_fin,
            estado_nombre,
            estado_desc
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        event_id,
        cambio.fecha_hora_inicio,   # Cadena o ISO-8601
        cambio.fecha_hora_fin,      # Cadena o None
        cambio.estado.nombre,
        cambio.estado.descripcion
    ))
    conn.commit()
    conn.close()

# ------------ Cargar un Evento por su ID (incluye series y muestras) ------------

def cargar_evento_por_id(id_evento: int) -> EventoSismico:
    conn = get_connection()
    c = conn.cursor()

    # 1) Leer la fila base del evento
    row = c.execute("SELECT * FROM Evento WHERE id_evento = ?", (id_evento,)).fetchone()
    if not row:
        conn.close()
        return None

    # 2) Reconstruir el objeto EventoSismico
    ubic    = UbicacionEvento((row["epicentro_lat"], row["epicentro_lng"]), row["hipocentro"])
    alcance = AlcanceSismo(row["alcance_nombre"], row["alcance_desc"])
    clasif  = ClasificacionSismo(row["clasif_desde"], row["clasif_hasta"], row["clasif_nombre"])
    origen  = OrigenDeGeneracion(row["origen_nombre"], row["origen_desc"])
    evento  = EventoSismico(
        row["id_evento"],
        row["fecha_hora"],
        ubic,
        str(row["magnitud"]) if row["magnitud"] is not None else "",
        alcance,
        clasif,
        origen
    )
    evento.estado = Estado(row["estado_nombre"], row["estado_desc"])

    # ——————————————
    # 2.b) Cargar historial de cambios de estado para este evento:
    cambio_rows = c.execute("""
        SELECT fecha_inicio, fecha_fin, estado_nombre, estado_desc
        FROM CambioEstado
        WHERE id_evento = ?
        ORDER BY fecha_inicio
    """, (id_evento,)).fetchall()

    for cr in cambio_rows:
        fecha_inicio = cr["fecha_inicio"]
        fecha_fin    = cr["fecha_fin"]
        est_nom      = cr["estado_nombre"]
        est_desc     = cr["estado_desc"]

        est_obj    = Estado(est_nom, est_desc)
        cambio_obj = CambioEstado(fecha_inicio, est_obj, fecha_fin)
        evento.cambios.append(cambio_obj)
    # ——————————————

    # 3) Cargar todas las series temporales vinculadas a este evento
    series_rows = c.execute("""
        SELECT id_serie, estacion, fecha_registro
        FROM SerieTemporal
        WHERE id_evento = ?
    """, (id_evento,)).fetchall()

    for s_row in series_rows:
        serie = SerieTemporal(s_row["estacion"], s_row["fecha_registro"], [])
        id_serie = s_row["id_serie"]

        # 4) Cargar las muestras de cada serie
        muestras_rows = c.execute("""
            SELECT fecha_muestra, velocidad_onda, frecuencia_onda, longitud_onda
            FROM MuestraSismica
            WHERE id_serie = ?
        """, (id_serie,)).fetchall()

        for m_row in muestras_rows:
            muestra = MuestraSismica(
                m_row["fecha_muestra"],
                m_row["velocidad_onda"],
                m_row["frecuencia_onda"],
                m_row["longitud_onda"]
            )
            serie.muestras.append(muestra)

        evento.series_temporales.append(serie)

    conn.close()
    return evento

