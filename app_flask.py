from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
import os

# Importamos nuestro dominio y gestor
from indexClases import (
    Estado,
    AnalistaEnSismos,
    UbicacionEvento,
    MuestraSismica,
    SerieTemporal,
    ClasificacionSismo,
    AlcanceSismo,
    OrigenDeGeneracion,
    EventoSismico
)
from gestorRegistro import GestorRegistrarResultado

# Importamos las funciones de persistencia y de inicialización de la BD
from repository import (
    guardar_evento,
    guardar_cambio_estado,
    cargar_evento_por_id
)
from db import init_db, get_connection  # CORRECCIÓN: init_db y get_connection vienen de db.py

# Stub para generar sismograma
def generar_sismograma(estacion, serie):
    return f"Sismograma generado correctamente para {estacion} ({serie.fecha_hora_registro})"

app = Flask(__name__)
app.config['analista'] = None

# Ruta absoluta a la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), 'sismos.db')

# ----------------------------------------
# Función para inicializar datos de ejemplo (seed)
# ----------------------------------------
def seed_data():
    # Borrar la base de datos existente si existe
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    # Reconstruir esquemas (crea tablas si no existen)
    init_db()

    # Insertar eventos de ejemplo
    analista = app.config['analista']

    # Ejemplo 1
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
    # Serie temporal con una muestra
    serie1 = SerieTemporal("Estación A", "2025-05-29 10:10", [
        MuestraSismica("2025-05-29 10:10:00", 5.2, 1.2, 0.4)
    ])
    ev1.series_temporales.append(serie1)
    guardar_evento(ev1)

    # Ejemplo 2
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

    # Ejemplo 3
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

# ----------------------------------------
# Rutas de Flask
# ----------------------------------------

@app.route('/')
def index():
    """
    Página de inicio con listado de eventos pendientes y botón de reseed
    """
    # Cargar eventos cuyo estado sea "AutoDetectado"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_evento FROM Evento;")
    filas = cur.fetchall()
    conn.close()

    eventos_pendientes = []
    for fila in filas:
        ev = cargar_evento_por_id(fila[0])
        if ev and ev.estado.getNombre() == "AutoDetectado":
            eventos_pendientes.append(ev)

    return render_template('lista_eventos.html', eventos=eventos_pendientes)

@app.route('/reseed', methods=['POST'])
def reseed():
    """
    Ruta para reconstruir la base de datos de cero con datos de ejemplo.
    """
    seed_data()
    return redirect(url_for('index'))

@app.route('/event/<int:event_id>', methods=['GET', 'POST'])
def detalle(event_id):
    analista = app.config['analista']
    evento = cargar_evento_por_id(event_id)
    if not evento:
        return redirect(url_for('index'))

    # Bloqueo inicial
    if evento.estado.getNombre() == "AutoDetectado":
        evento.bloquearParaRevision(analista)
        guardar_evento(evento)
        guardar_cambio_estado(event_id, evento.cambios[-1])

    error = None
    if request.method == 'POST':
        accion = request.form.get('accion')

        # Modificar datos del evento
        if accion == 'update':
            mag = request.form.get('magnitud', '').strip()
            alc = request.form.get('alcance', '').strip()
            ori = request.form.get('origen', '').strip()

            if not mag or not alc or not ori:
                error = "Magnitud, Alcance y Origen son obligatorios."
                return render_template('detalle_evento.html', evento=evento, error=error)

            evento.magnitud = mag
            evento.alcance = AlcanceSismico(alc, alc)
            evento.origen = OrigenDeGeneracion(ori)
            guardar_evento(evento)
            return redirect(url_for('detalle', event_id=event_id))

        # Acciones de revisión
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

# ----------------------------------------
# Ejecución principal
# ----------------------------------------

def main():
    analista = AnalistaEnSismos("María Pérez", "maria.perez@ccrs.gov.ar")
    app.config['analista'] = analista

    # Inicializar BD y datos de ejemplo si no existe
    if not os.path.exists(DB_PATH):
        seed_data()

    app.run(debug=True)

if __name__ == '__main__':
    main()
