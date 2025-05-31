from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for

# Importamos nuestro dominio y gestor
from indexClases import (
    Estado,
    Usuario,
    AnalistaEnSismos,
    UbicacionEvento,
    MuestraSismica,
    SerieTemporal,
    ClasificacionSismo,
    OrigenDeGeneracion,
    EventoSismico
)
from gestorRegistro import GestorRegistrarResultado

# Stub para generar sismograma (igual al original)
def generar_sismograma(estacion, serie):
    return f"Sismograma generado correctamente para {estacion} ({serie.fecha_hora_registro})"

# ----------------------------------------
# Plantillas HTML en formato string (Jinja2)
# ----------------------------------------

HTML_LIST = '''
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Listado de Eventos</title>
  <style>
    body { font:14px Arial, sans-serif; margin:20px; }
    table { width:100%; border-collapse:collapse; margin-top:20px; }
    th, td { border:1px solid #ccc; padding:8px; text-align:left; }
    th { background:#f0f0f0; }
    tr:hover { background:#f9f9f9; cursor:pointer; }
    h1 { margin-bottom:10px; }
    a { text-decoration:none; color:#0066cc; }
  </style>
</head>
<body>
  <h1>Listado de Eventos Pendientes</h1>
  {% if eventos %}
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Fecha y Hora</th>
          <th>Epicentro</th>
          <th>Hipocentro</th>
          <th>Magnitud</th>
          <th>Estado</th>
        </tr>
      </thead>
      <tbody>
      {% for ev in eventos %}
        <tr onclick="window.location='{{ url_for('detalle', event_id=ev.id_evento) }}'">
          <td>{{ ev.id_evento }}</td>
          <td>{{ ev.fecha_hora }}</td>
          <td>{{ ev.ubicacion.epicentro }}</td>
          <td>{{ ev.ubicacion.hipocentro }} km</td>
          <td>{{ ev.magnitud }}</td>
          <td>{{ ev.estado.nombre }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  {% else %}
    <p>No hay eventos pendientes de revisión.</p>
  {% endif %}
</body>
</html>
'''

HTML_DETAIL = '''
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Detalle Evento {{ evento.id_evento }}</title>
  <style>
    body { font:14px Arial, sans-serif; margin:20px; }
    section { margin-bottom:20px; }
    h2 { margin-top:30px; }
    table { width:100%; border-collapse:collapse; margin-top:10px; }
    th, td { border:1px solid #ccc; padding:6px; }
    th { background:#f0f0f0; }
    label { display:block; margin-top:8px; }
    input[type=text] { padding:4px; width:300px; }
    button { margin:6px; padding:6px 12px; }
    .error { color:red; }
    a { text-decoration:none; color:#0066cc; }
  </style>
</head>
<body>
  <h1>Detalle del Evento {{ evento.id_evento }}</h1>

  <!-- Sección: Datos básicos del evento -->
  <section>
    <p><strong>Fecha/Hora:</strong> {{ evento.fecha_hora }}</p>
    <p><strong>Ubicación:</strong> Epicentro ({{ evento.ubicacion.epicentro }}) – 
       Hipocentro ({{ evento.ubicacion.hipocentro }} km)</p>
    <p><strong>Magnitud:</strong> {{ evento.magnitud }}</p>
    <p><strong>Clasificación:</strong> {{ evento.clasificacion }}</p>
    <p><strong>Alcance:</strong> {{ evento.alcance }}</p>
    <p><strong>Origen:</strong> {{ evento.origen }}</p>
    <p><strong>Estado Actual:</strong> {{ evento.estado.nombre }}</p>
  </section>

  {% if error %}
    <p class="error">{{ error }}</p>
  {% endif %}

  <!-- Sección: Modificar datos del evento -->
  <section>
    <h2>Modificar Datos del Evento</h2>
    <form method="post" action="{{ url_for('detalle', event_id=evento.id_evento) }}">
      <input type="hidden" name="accion" value="update">
      <label>Magnitud (número): <input name="magnitud" value="{{ evento.magnitud }}"></label>
      <label>Alcance: <input name="alcance" value="{{ evento.alcance }}"></label>
      <label>Origen (tipo): <input name="origen" value="{{ evento.origen.tipo }}"></label>
      <button type="submit" onclick="return confirm('¿Guardar cambios de magnitud/alcance/origen?')">
        Guardar Cambios
      </button>
    </form>
  </section>

  <!-- Sección: Acciones de revisión -->
  <section>
    <h2>Acciones de Revisión</h2>
    <form method="post" action="{{ url_for('detalle', event_id=evento.id_evento) }}">
      <button name="accion" value="confirm" 
              onclick="return confirm('¿Confirmar evento?')">
        ✔ Confirmar Evento
      </button>
      <button name="accion" value="reject" 
              onclick="return confirm('¿Rechazar evento?')">
        ✖ Rechazar Evento
      </button>
      <button name="accion" value="expert" 
              onclick="return confirm('¿Solicitar revisión a experto?')">
        🕵 Solicitar Revisión a Experto
      </button>
    </form>
  </section>

  <!-- Sección: Opciones adicionales -->
  <section>
    <h2>Opciones Adicionales</h2>
    <form method="get" action="{{ url_for('mostrar_mapa', event_id=evento.id_evento) }}">
      <button type="submit" onclick="return confirm('¿Visualizar mapa?')">🗺 Mostrar Mapa</button>
    </form>
  </section>

  <!-- Sección: Series Temporales y Muestras -->
  <section>
    <h2>Series Temporales y Muestras</h2>
    {% if evento.series_temporales %}
      {% for s in evento.series_temporales %}
        <h3>Estación: {{ s.estacion }} (Registro: {{ s.fecha_hora_registro }})</h3>
        <table>
          <thead>
            <tr>
              <th>Tiempo</th><th>Velocidad (km/s)</th><th>Frecuencia (Hz)</th><th>Longitud (km)</th>
            </tr>
          </thead>
          <tbody>
            {% for m in s.muestras %}
              <tr>
                <td>{{ m.fecha_hora_muestra }}</td>
                <td>{{ m.velocidad_onda }}</td>
                <td>{{ m.frecuencia_onda }}</td>
                <td>{{ m.longitud_onda }}</td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      {% endfor %}
    {% else %}
      <p>No hay series temporales registradas.</p>
    {% endif %}
  </section>

  <!-- Sección: Historial de Estados -->
  <section>
    <h2>Historial de Estados</h2>
    {% if evento.cambios %}
      <ul>
      {% for c in evento.cambios %}
        <li>{{ c }}</li>
      {% endfor %}
      </ul>
    {% else %}
      <p>No hay cambios de estado registrados.</p>
    {% endif %}
  </section>

  <p><a href="{{ url_for('index') }}">← Volver al Listado</a></p>
</body>
</html>
'''

HTML_MAP = '''
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Mapa del Evento {{ evento.id_evento }}</title>
  <style>
    body { font:14px Arial, sans-serif; margin:20px; }
    #map { width:100%; height:400px; background:#eee; 
           text-align:center; line-height:400px; color:#666; }
    a { text-decoration:none; color:#0066cc; }
  </style>
</head>
<body>
  <h1>Mapa del Evento {{ evento.id_evento }}</h1>
  <div id="map">
    <!-- Aquí podrías cargar un iframe/JS real; esto es un stub -->
    [Stub de mapa: epicentro {{ evento.ubicacion.epicentro }} y estaciones cercanas]
  </div>
  <p><a href="{{ url_for('detalle', event_id=evento.id_evento) }}">← Volver</a></p>
</body>
</html>
'''

# ----------------------------------------
# Configuración y rutas de Flask
# ----------------------------------------

app = Flask(__name__)

# Almacenamos el analista y los eventos en app.config
app.config['analista'] = None
app.config['eventos'] = []

@app.route('/')
def index():
    """
    Lista únicamente los eventos cuyo estado sea "AutoDetectado"
    (pendientes de revisión).
    """
    gestor = GestorRegistrarResultado(
        app.config['eventos'],
        [],     # No requerimos estaciones/sismógrafos aquí
        [],
        app.config['analista']
    )
    pendientes = gestor.obtenerEventosNoRevisados()
    return render_template_string(HTML_LIST, eventos=pendientes)

@app.route('/event/<int:event_id>', methods=['GET', 'POST'])
def detalle(event_id):
    analista = app.config['analista']
    evento = next((e for e in app.config['eventos'] if e.id_evento == event_id), None)
    if not evento:
        return redirect(url_for('index'))

    # 1) Bloqueo inicial: si está en AutoDetectado, lo bloqueamos
    if evento.estado.nombre == "AutoDetectado":
        evento.bloquearParaRevision(analista)

    error = None

    if request.method == 'POST':
        accion = request.form.get('accion')

        # --- Modificar datos del evento ---
        if accion == 'update':
            mag = request.form.get('magnitud', '').strip()
            alc = request.form.get('alcance', '').strip()
            ori = request.form.get('origen', '').strip()

            if not mag or not alc or not ori:
                error = "Magnitud, Alcance y Origen son obligatorios."
                return render_template_string(HTML_DETAIL, evento=evento, error=error)

            # Actualizamos usando nuestro modelo
            evento.magnitud = mag
            evento.alcance = alc
            evento.origen = OrigenDeGeneracion(ori)
            return redirect(url_for('detalle', event_id=event_id))

        # --- Acciones de revisión ---
        if accion in ['confirm', 'reject', 'expert']:
            if accion == 'confirm':
                nuevo_estado = Estado("Confirmado", "Confirmado por analista")
                evento.cambiarEstado(nuevo_estado)
            elif accion == 'reject':
                evento.rechazar()
            else:  # 'expert'
                nuevo_estado = Estado("Derivado a experto", "Derivado a analista supervisor")
                evento.cambiarEstado(nuevo_estado)

            return redirect(url_for('detalle', event_id=event_id))

    return render_template_string(HTML_DETAIL, evento=evento, error=error)

@app.route('/map/<int:event_id>')
def mostrar_mapa(event_id):
    evento = next((e for e in app.config['eventos'] if e.id_evento == event_id), None)
    if not evento:
        return redirect(url_for('index'))
    return render_template_string(HTML_MAP, evento=evento)

@app.route('/sismograma/<int:event_id>/<estacion>', methods=['POST'])
def sismograma(event_id, estacion):
    evento = next((e for e in app.config['eventos'] if e.id_evento == event_id), None)
    if not evento:
        return redirect(url_for('index'))

    # Buscamos la serie que coincida con la estación dada
    serie = next((s for s in evento.series_temporales if s.estacion == estacion), None)
    if not serie:
        return f"<p>No se encontró la serie para estación {estacion}.</p>" \
               f"<p><a href='{url_for('detalle', event_id=event_id)}'>← Volver</a></p>"

    mensaje = generar_sismograma(estacion, serie)
    return f"<p>{mensaje}</p><p><a href='{url_for('detalle', event_id=event_id)}'>← Volver</a></p>"

# ----------------------------------------
# Ejecución principal
# ----------------------------------------

def main():
    # 1) Creamos un analista (en un sistema real se obtendría del login)
    analista = AnalistaEnSismos("María Pérez", "maria.perez@ccrs.gov.ar")

    # 2) Creamos algunos eventos de ejemplo
    eventos_demo = []

    # Ejemplo 1
    ubi1 = UbicacionEvento((24.123, -65.987), 10.5)
    ev1 = EventoSismico(
        23,
        "2025-05-29 10:15",
        ubi1,
        "4.2",             # magnitud (string en este ejemplo)
        "Regional",        # alcance (string)
        ClasificacionSismo(61, 300, "Intermedio"),
        OrigenDeGeneracion("Tectónico", "Movimiento de placas")
    )
    # Serie temporal con una muestra
    serie1 = SerieTemporal("Estación A", "2025-05-29 10:10", [
        MuestraSismica("2025-05-29 10:10:00", 5.2, 1.2, 0.4)
    ])
    ev1.series_temporales.append(serie1)
    eventos_demo.append(ev1)

    # Ejemplo 2
    ev2 = EventoSismico(
        24,
        "2025-05-30 11:20",
        UbicacionEvento((35.678, -58.345), 15.2),
        "5.1",
        "Local",
        ClasificacionSismo(0, 60, "Baja"),
        OrigenDeGeneracion("Volcánico", "Erupción")
    )
    eventos_demo.append(ev2)

    # Ejemplo 3
    ev3 = EventoSismico(
        25,
        "2025-05-30 12:05",
        UbicacionEvento((12.345, -45.678), 8.9),
        "3.8",
        "Local",
        ClasificacionSismo(0, 30, "Muy Baja"),
        OrigenDeGeneracion("Artificial", "Pruebas humanas")
    )
    eventos_demo.append(ev3)

    # Guardamos en la configuración de Flask
    app.config['analista'] = analista
    app.config['eventos'] = eventos_demo

    # Arrancamos el servidor en modo debug
    app.run(debug=True)

if __name__ == '__main__':
    main()
