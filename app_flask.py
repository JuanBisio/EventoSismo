from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

# Importar las clases y el gestor
from indexClases import (
    EventoSismico, UbicacionEvento, MagnitudRichter, AlcanceSismo,
    ClasificacionSismo, OrigenDeGeneracion, MuestraSismica, SerieTemporal,
    EstacionSismologica, Sismografo, Estado, Usuario, AnalistaEnSismos
)
from gestorRegistro import GestorRegistrarResultado

app = Flask(__name__)

# ------------------------------------
# Simulación de "bases de datos" en memoria
# ------------------------------------
eventos_db = []
estaciones_db = []
sismografos_db = []

# 1) Analista que estará "logueado"
analista_actual = AnalistaEnSismos("Ana Gómez", "ana.gomez@mail.com", datetime.now(), "pwd123")

# 2) Crear estaciones y sismógrafos de ejemplo
est1 = EstacionSismologica(1, "Estación Norte", "DOC123", "2025-01-15", -34.60, -58.38, "CERT456")
est2 = EstacionSismologica(2, "Estación Sur", "DOC789", "2025-02-10", -32.15, -64.50, "CERT999")
estaciones_db.extend([est1, est2])

sis1 = Sismografo(1, "SismoPro X", "Alta precisión", "SN-001", est1)
sis2 = Sismografo(2, "SismoLite", "Baja precisión", "SN-002", est2)
sismografos_db.extend([sis1, sis2])

# 3) Crear un Evento sísmico con su serie temporal y muestra (no revisado)
ubicA = UbicacionEvento((24.123, -65.987), 10.5)
magA = MagnitudRichter(4.2, "Leve", "Richter")
clasA = ClasificacionSismo(30, 60, "Intermedio")
alcA = AlcanceSismo("Detectable en varias provincias", "Medio Alcance")
oriA = OrigenDeGeneracion("Tectónico", "Movimiento de placas")
evA = EventoSismico(101, "2025-05-29 10:15", ubicA, magA, alcA, clasA, oriA)

m1 = MuestraSismica("2025-05-29 10:10:00", 5.2, 1.2, 0.4)
serieA = SerieTemporal("Normal", "2025-05-29 10:10", 100, [m1])
evA.agregarSerieTemporal(serieA)
eventos_db.append(evA)

# ------------------------------------
# Rutas de Flask
# ------------------------------------

@app.route("/")
def home():
    return redirect(url_for("listar_eventos"))


@app.route("/revisar-eventos")
def listar_eventos():
    """
    Muestra la lista de eventos sísmicos no revisados (estado 'AutoDetectado').
    """
    gestor = GestorRegistrarResultado(eventos_db, estaciones_db, sismografos_db, analista_actual)
    sin_revisar = gestor.obtenerEventosNoRevisados()
    return render_template("lista_eventos.html", eventos=sin_revisar)


@app.route("/detalle-evento/<int:id_evento>")
def detalle_evento(id_evento):
    """
    Bloquea el evento para revisión (cambia a 'BloqueadoEnRevision'),
    obtiene sus datos sísmicos (alcance, clasificación, origen, series/muestras y sismogramas),
    y los pasa a la plantilla para mostrar.
    """
    gestor = GestorRegistrarResultado(eventos_db, estaciones_db, sismografos_db, analista_actual)
    try:
        evento_sel = gestor.seleccionarEvento(id_evento)
    except ValueError:
        return "Evento no encontrado", 404

    datos = gestor.obtenerDatosSismicos(evento_sel)
    return render_template("detalle_evento.html", evento=evento_sel, datos=datos)


@app.route("/accion-evento", methods=["POST"])
def accion_evento():
    """
    Recibe el formulario con los datos de acción: 
      - evento_id: ID del evento
      - accion: 'Confirmar', 'Rechazar' o 'SolicitarExperto'
      - opcionalmente, campos para modificar magnitud, alcance u origen
    Invoca al gestor para aplicar la acción y redirige a la lista.
    """
    id_e = int(request.form.get("evento_id"))
    accion = request.form.get("accion")  # 'Confirmar', 'Rechazar' o 'SolicitarExperto'

    gestor = GestorRegistrarResultado(eventos_db, estaciones_db, sismografos_db, analista_actual)
    try:
        evento_sel = gestor.seleccionarEvento(id_e)
    except ValueError:
        return "Evento no encontrado", 404

    # Si el analista marcó \"modificar\" en el formulario, se obtienen los nuevos valores
    if request.form.get("modificar") == "true":
        # Magnitud (número, descripción, unidad)
        mag_nueva = request.form.get("magnitud_numero")
        if mag_nueva:
            descr = request.form.get("magnitud_desc")
            unidad = request.form.get("magnitud_unidad")
            nueva_mag = MagnitudRichter(float(mag_nueva), descr, unidad)
        else:
            nueva_mag = None

        # Alcance (nombre, descripción)
        alc_nuevo = request.form.get("alcance_nombre")
        if alc_nuevo:
            desc_alc = request.form.get("alcance_desc")
            nuevo_alc = AlcanceSismo(desc_alc, alc_nuevo)
        else:
            nuevo_alc = None

        # Origen (nombre, descripción)
        ori_nuevo = request.form.get("origen_nombre")
        if ori_nuevo:
            desc_ori = request.form.get("origen_desc")
            nuevo_ori = OrigenDeGeneracion(ori_nuevo, desc_ori)
        else:
            nuevo_ori = None

        gestor.permitirModificacionDatos(evento_sel, nueva_mag, nuevo_alc, nuevo_ori)

    # Registrar la acción final (Confirmar, Rechazar o SolicitarExperto)
    try:
        gestor.registrarAccion(evento_sel, accion)
    except ValueError as e:
        return f"Error: {str(e)}", 400

    return redirect(url_for("listar_eventos"))


if __name__ == "__main__":
    app.run(debug=True)
