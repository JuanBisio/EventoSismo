from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

# Importamos nuestro dominio y repositorio
from indexClases import (
    Estado,
    AnalistaEnSismos,
    UbicacionEvento,
    MuestraSismica,
    SerieTemporal,
    ClasificacionSismo,
    AlcanceSismo,            # ¡importar AlcanceSismo!
    OrigenDeGeneracion,
    EventoSismico
)
from gestorRegistro import GestorRegistrarResultado
from repository import guardar_evento, guardar_cambio_estado, cargar_evento_por_id

# Stub para generar sismograma
def generar_sismograma(estacion, serie):
    return f"Sismograma generado correctamente para {estacion} ({serie.fecha_hora_registro})"

app = Flask(__name__)

# Sólo guardamos el analista en la configuración; los eventos los cargamos de SQLite
app.config['analista'] = None

@app.route('/')
def index():
    """
    Lista únicamente los eventos cuyo estado sea "AutoDetectado" (pendientes de revisión).
    """
    # Cargar todos los eventos y filtrar por estado "AutoDetectado"
    eventos_pendientes = []
    conn = cargar_evento_por_id.__globals__['get_connection']()  # abrimos conexión sqlite
    cursor = conn.cursor()
    cursor.execute("SELECT id_evento FROM Evento;")
    filas = cursor.fetchall()
    for fila in filas:
        ev = cargar_evento_por_id(fila["id_evento"])
        if ev and ev.estado.getNombre() == "AutoDetectado":
            eventos_pendientes.append(ev)
    conn.close()

    return render_template('lista_eventos.html', eventos=eventos_pendientes)

@app.route('/event/<int:event_id>', methods=['GET', 'POST'])
def detalle(event_id):
    analista = app.config['analista']
    # Cargamos el evento desde la BD
    evento = cargar_evento_por_id(event_id)
    if not evento:
        return redirect(url_for('index'))

    # 1) Bloqueo inicial: si está en AutoDetectado, lo bloqueamos
    if evento.estado.getNombre() == "AutoDetectado":
        evento.bloquearParaRevision(analista)
        # Persistimos el cambio de estado
        guardar_evento(evento)
        guardar_cambio_estado(event_id, evento.cambios[-1])

    error = None

    if request.method == 'POST':
        accion = request.form.get('accion')

        # --- Modificar datos del evento ---
        if accion == 'update':
            mag = request.form.get('magnitud', '').strip()
            alc = request.form.get('alcance', '').strip()
            ori = request.form.get('origen', '').strip()

            # Validación básica
            if not mag or not alc or not ori:
                error = "Magnitud, Alcance y Origen son obligatorios."
                return render_template('detalle_evento.html', evento=evento, error=error)

            # Actualizamos el objeto en memoria
            evento.magnitud = mag
            evento.alcance = AlcanceSismo(alc, alc)  # Tanto nombre como descripción hemos dejado igual
                                                # (puedes modificar si quieres separar desc/nombre)
            evento.origen = OrigenDeGeneracion(ori)

            # Guardamos los cambios en la base de datos
            guardar_evento(evento)
            return redirect(url_for('detalle', event_id=event_id))

        # --- Acciones de revisión ---
        if accion in ['confirm', 'reject', 'expert']:
            if accion == 'confirm':
                nuevo_estado = Estado("Confirmado", "Confirmado por analista")
                evento.cambiarEstado(nuevo_estado)
                guardar_evento(evento)
                guardar_cambio_estado(event_id, evento.cambios[-1])

            elif accion == 'reject':
                evento.rechazar()
                guardar_evento(evento)
                guardar_cambio_estado(event_id, evento.cambios[-1])

            else:  # 'expert'
                nuevo_estado = Estado("Derivado a experto", "Derivado a analista supervisor")
                evento.cambiarEstado(nuevo_estado)
                guardar_evento(evento)
                guardar_cambio_estado(event_id, evento.cambios[-1])

            return redirect(url_for('detalle', event_id=event_id))

    return render_template('detalle_evento.html', evento=evento, error=error)

@app.route('/map/<int:event_id>')
def mostrar_mapa(event_id):
    evento = cargar_evento_por_id(event_id)
    if not evento:
        return redirect(url_for('index'))
    return render_template('mapa.html', evento=evento)

@app.route('/sismograma/<int:event_id>/<estacion>', methods=['POST'])
def sismograma(event_id, estacion):
    evento = cargar_evento_por_id(event_id)
    if not evento:
        return redirect(url_for('index'))

    serie = next((s for s in evento.series_temporales if s.estacion == estacion), None)
    if not serie:
        return (
            f"<p>No se encontró la serie para estación {estacion}.</p>"
            f"<p><a href='{url_for('detalle', event_id=event_id)}'>← Volver</a></p>"
        )

    mensaje = generar_sismograma(estacion, serie)
    return (
        f"<p>{mensaje}</p>"
        f"<p><a href='{url_for('detalle', event_id=event_id)}'>← Volver</a></p>"
    )

def main():
    # 1) Creamos un analista (en un sistema real, vendría del login)
    analista = AnalistaEnSismos("María Pérez", "maria.perez@ccrs.gov.ar")
    app.config['analista'] = analista

    # 2) Creamos algunos eventos de ejemplo SOLO SI NO EXISTEN
    if not cargar_evento_por_id(23):
        ubi1 = UbicacionEvento((24.123, -65.987), 10.5)
        ev1 = EventoSismico(
            23,
            "2025-05-29 10:15",
            ubi1,
            "4.2",
            AlcanceSismo("Detectable en varias provincias", "Regional"),
            ClasificacionSismo(61, 300, "Intermedio"),
            OrigenDeGeneracion("Tectónico", "Movimiento de placas")
        )
        # Agregamos una serie temporal con una muestra
        serie1 = SerieTemporal("Estación A", "2025-05-29 10:10", [
            MuestraSismica("2025-05-29 10:10:00", 5.2, 1.2, 0.4)
        ])
        ev1.series_temporales.append(serie1)
        # Guardamos en SQLite
        guardar_evento(ev1)

    if not cargar_evento_por_id(24):
        ev2 = EventoSismico(
            24,
            "2025-05-30 11:20",
            UbicacionEvento((35.678, -58.345), 15.2),
            "5.1",
            AlcanceSismo("Localmente perceptible", "Local"),
            ClasificacionSismo(0, 60, "Baja"),
            OrigenDeGeneracion("Volcánico", "Erupción")
        )
        guardar_evento(ev2)

    if not cargar_evento_por_id(25):
        ev3 = EventoSismico(
            25,
            "2025-05-30 12:05",
            UbicacionEvento((12.345, -45.678), 8.9),
            "3.8",
            AlcanceSismo("Muy local", "Muy Local"),
            ClasificacionSismo(0, 30, "Muy Baja"),
            OrigenDeGeneracion("Artificial", "Pruebas humanas")
        )
        guardar_evento(ev3)

    app.run(debug=True)

if __name__ == '__main__':
    main()
