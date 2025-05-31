# registro_revision_manual.py
# Implementación web del Caso de Uso 23: Registrar resultado de revisión manual,
# al aceptar acciones, permanece en la página de detalle y actualiza historial.

from datetime import datetime
import sys
try:
    from flask import Flask, render_template_string, request, redirect, url_for
    WEB_UI = True
except ImportError:
    WEB_UI = False

# -------------------- Modelo de Dominio --------------------
class Estado:
    def __init__(self, nombre, descripcion=""):
        self.nombre = nombre
        self.descripcion = descripcion
    def __str__(self): return f"{self.nombre}: {self.descripcion}"

class CambioEstado:
    def __init__(self, fecha_revision, analista, estado, observacion=None):
        self.fecha_revision = fecha_revision
        self.analista = analista
        self.estado = estado
        self.observacion = observacion
    def __str__(self):
        obs = f" (obs: {self.observacion})" if self.observacion else ""
        ts = self.fecha_revision.strftime('%Y-%m-%d %H:%M:%S')
        return f"[{ts}] {self.analista.nombre} -> {self.estado.nombre}{obs}"

class Usuario:
    def __init__(self, nombre, mail, contrasena=None):
        self.nombre = nombre
        self.mail = mail
        self.contrasena = contrasena

class AnalistaEnSismos(Usuario): pass

class UbicacionEvento:
    def __init__(self, epicentro, hipocentro):
        self.epicentro = epicentro
        self.hipocentro = hipocentro
    def __str__(self): return f"Epicentro: {self.epicentro}, Hipocentro: {self.hipocentro} km"

class Muestra:
    def __init__(self, fecha_hora, velocidad_onda, frecuencia_onda, longitud):
        self.fecha_hora = fecha_hora
        self.velocidad_onda = velocidad_onda
        self.frecuencia_onda = frecuencia_onda
        self.longitud = longitud

class SerieTemporal:
    def __init__(self, estacion, fecha_registro, muestras=None):
        self.estacion = estacion
        self.fecha_registro = fecha_registro
        self.muestras = muestras or []

class ClasificacionEvento:
    def __init__(self, nombre, descripcion=""):
        self.nombre = nombre
        self.descripcion = descripcion
    def __str__(self): return f"{self.nombre} ({self.descripcion})"

class OrigenGeneracion:
    def __init__(self, tipo, descripcion=""):
        self.tipo = tipo
        self.descripcion = descripcion
    def __str__(self): return f"{self.tipo}: {self.descripcion}"

class EventoSismico:
    def __init__(self, id_evento, fecha_hora, ubicacion, magnitud,
                 alcance, clasificacion, origen):
        self.id_evento = id_evento
        self.fecha_hora = fecha_hora
        self.ubicacion = ubicacion
        self.magnitud = magnitud
        self.alcance = alcance
        self.clasificacion = clasificacion
        self.origen = origen
        self.estado = Estado("AutoDetectado", "Detectado automáticamente")
        self.cambios = []
        self.series = []

    def bloquear_para_revision(self, analista):
        nuevo = Estado("Bloqueado en revisión", "Bloqueado para revisión manual")
        self.estado = nuevo
        self.cambios.append(CambioEstado(datetime.now(), analista, nuevo))

    def actualizar_estado(self, estado, analista, obs=None):
        self.estado = estado
        self.cambios.append(CambioEstado(datetime.now(), analista, estado, obs))
        # permanece en detalle para mostrar nuevo estado

# Stub sismograma
def generar_sismograma(estacion, serie):
    return f"Sismograma generado correctamente para {estacion} ({serie.fecha_registro})"

# -------------------- Templates --------------------
if WEB_UI:
    HTML_LIST = '''
    <!doctype html>
    <html><head><meta charset="utf-8"><title>Listado de Eventos</title>
      <style>body{font:14px Arial;margin:20px;}table{width:100%;border-collapse:collapse;}th,td{border:1px solid #ccc;padding:6px;}th{background:#eee;}tr:hover{background:#f9f9f9;cursor:pointer;}</style>
    </head><body>
      <h1>Listado de Eventos</h1>
      <table>
        <thead><tr><th>ID</th><th>Fecha y Hora</th><th>Epicentro</th><th>Hipocentro</th><th>Magnitud</th><th>Estado</th></tr></thead>
        <tbody>
        {% for ev in eventos %}
          <tr onclick="location.href='{{ url_for('detalle', event_id=ev.id_evento) }}'">
            <td>{{ ev.id_evento }}</td>
            <td>{{ ev.fecha_hora }}</td>
            <td>{{ ev.ubicacion.epicentro }}</td>
            <td>{{ ev.ubicacion.hipocentro }}</td>
            <td>{{ ev.magnitud }}</td>
            <td>{{ ev.estado.nombre }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </body></html>
    '''

    HTML_DETAIL = '''
    <!doctype html>
    <html><head><meta charset="utf-8"><title>Detalle Evento {{ evento.id_evento }}</title>
      <style>body{font:14px Arial;margin:20px;}section{margin-bottom:20px;}h2{margin-top:30px;}table{width:100%;border-collapse:collapse;}th,td{border:1px solid #ccc;padding:6px;}label{display:block;margin-top:8px;}input{padding:4px;width:300px;}button{margin:6px;padding:6px 12px;} .error{color:red;}</style>
    </head><body>
      <h1>Detalle del Evento {{ evento.id_evento }}</h1>
      <section>
        <p><strong>Fecha y Hora:</strong> {{ evento.fecha_hora }}</p>
        <p><strong>Ubicación:</strong> {{ evento.ubicacion }}</p>
        <p><strong>Estado Actual:</strong> {{ evento.estado.nombre }}</p>
      </section>
      {% if error %}<p class="error">{{ error }}</p>{% endif %}
      <section>
        <h2>Modificar Datos del Evento</h2>
        <form method="post" action="{{ url_for('detalle', event_id=evento.id_evento) }}">
          <input type="hidden" name="accion" value="update">
          <label>Magnitud:<input name="magnitud" value="{{ evento.magnitud }}"></label>
          <label>Alcance:<input name="alcance" value="{{ evento.alcance }}"></label>
          <label>Origen:<input name="origen" value="{{ evento.origen.tipo if evento.origen.__class__.__name__!='Estado' else evento.origen.nombre }}"></label>
          <button type="submit" onclick="return confirm('¿Guardar cambios de magnitud/alcance/origen?')">Guardar Cambios</button>
        </form>
      </section>
      <section>
        <h2>Acciones de Revisión</h2>
        <form method="post" action="{{ url_for('detalle', event_id=evento.id_evento) }}">
          <button name="accion" value="confirm" onclick="return confirm('¿Confirmar evento?')">Confirmar Evento</button>
          <button name="accion" value="reject" onclick="return confirm('¿Rechazar evento?')">Rechazar Evento</button>
          <button name="accion" value="expert" onclick="return confirm('¿Solicitar revisión a experto?')">Solicitar Revisión a Experto</button>
        </form>
      </section>
      <section>
        <h2>Opciones Adicionales</h2>
        <form method="get" action="{{ url_for('mostrar_mapa', event_id=evento.id_evento) }}">
          <button type="submit" onclick="return confirm('¿Visualizar mapa?')">Mostrar Mapa</button>
        </form>
      </section>
      <section>
        <h2>Series Temporales y Muestras</h2>
        {% for s in evento.series %}
          <h3>Estación: {{ s.estacion }} (Registro: {{ s.fecha_registro }})</h3>
          <table>
            <thead><tr><th>Tiempo</th><th>Velocidad</th><th>Frecuencia</th><th>Longitud</th></tr></thead>
            <tbody>
            {% for m in s.muestras %}
              <tr><td>{{ m.fecha_hora }}</td><td>{{ m.velocidad_onda }}</td><td>{{ m.frecuencia_onda }}</td><td>{{ m.longitud }}</td></tr>
            {% endfor %}
            </tbody>
          </table>
        {% endfor %}
      </section>
      <section>
        <h2>Historial de Estados</h2>
        <ul>
        {% for c in evento.cambios %}<li>{{ c }}</li>{% endfor %}
        </ul>
      </section>
      <p><a href="{{ url_for('index') }}">← Volver al listado</a></p>
    </body></html>
    '''

    HTML_MAP = '''
    <!doctype html>
    <html><head><meta charset="utf-8"><title>Mapa Evento {{ evento.id_evento }}</title>
      <style>#map{width:100%;height:400px;background:#eee;text-align:center;line-height:400px;color:#666;}body{font:14px Arial;margin:20px;}</style>
    </head><body>
      <h1>Mapa del Evento {{ evento.id_evento }}</h1>
      <div id="map">[Stub de mapa: epicentro {{ evento.ubicacion.epicentro }} y estaciones]</div>
      <p><a href="{{ url_for('detalle', event_id=evento.id_evento) }}">← Volver</a></p>
    </body></html>
    '''

    app = Flask(__name__)
    app.config['analista'] = None
    app.config['eventos'] = []

    @app.route('/')
    def index():
        return render_template_string(HTML_LIST, eventos=app.config['eventos'])

    @app.route('/event/<int:event_id>', methods=['GET','POST'])
    def detalle(event_id):
        analista = app.config['analista']
        evento = next((e for e in app.config['eventos'] if e.id_evento==event_id), None)
        if not evento:
            return redirect(url_for('index'))
        # Bloqueo inicial
        if evento.estado.nombre == "AutoDetectado":
            evento.bloquear_para_revision(analista)
        error = None
        if request.method == 'POST':
            accion = request.form.get('accion')
            if accion == 'update':
                mag = request.form.get('magnitud','').strip()
                alc = request.form.get('alcance','').strip()
                ori = request.form.get('origen','').strip()
                if not mag or not alc or not ori:
                    error = "Magnitud, alcance y origen son obligatorios."
                    return render_template_string(HTML_DETAIL, evento=evento, error=error)
                evento.magnitud, evento.alcance = mag, alc
                evento.origen = OrigenGeneracion(ori)
                # Stay on detail
                return redirect(url_for('detalle', event_id=event_id))
            if accion in ['confirm','reject','expert']:
                if accion == 'confirm':
                    est = Estado("Confirmado", "Confirmado por analista")
                elif accion == 'reject':
                    est = Estado("Rechazado", "Rechazado por analista")
                else:
                    est = Estado("Derivado a experto", "Derivado a analista supervisor")
                evento.actualizar_estado(est, analista)
                # Stay on detail to show new history entry
                return redirect(url_for('detalle', event_id=event_id))
        return render_template_string(HTML_DETAIL, evento=evento, error=None)

    @app.route('/map/<int:event_id>')
    def mostrar_mapa(event_id):
        evento = next((e for e in app.config['eventos'] if e.id_evento==event_id), None)
        if not evento:
            return redirect(url_for('index'))
        return render_template_string(HTML_MAP,evento=evento)

    @app.route('/sismograma/<int:event_id>/<estacion>', methods=['POST'])
    def sismograma(event_id, estacion):
        evento = next(e for e in app.config['eventos'] if e.id_evento==event_id)
        serie = next(s for s in evento.series if s.estacion==estacion)
        mensaje = generar_sismograma(estacion, serie)
        return f"<p>{mensaje}</p><p><a href='{url_for('detalle', event_id=event_id)}'>← Volver</a></p>"

# -------------------- Ejecución principal --------------------
def main():
    analista = AnalistaEnSismos("María Pérez","maria.perez@ccrs.gov.ar")
    # Ejemplos de eventos
    ubi1 = UbicacionEvento((24.123, -65.987),10.5)
    ev1 = EventoSismico(23,"2025-05-29 10:15",ubi1,"4.2","Regional",ClasificacionEvento("Intermedio","61-300 km"),OrigenGeneracion("Tectónico",""))
    ev1.series.append(SerieTemporal("Estación A","2025-05-29 10:10",[Muestra("10:10:00",5.2,1.2,0.4)]))
    ev2 = EventoSismico(24,"2025-05-30 11:20",UbicacionEvento((35.678,-58.345),15.2),"5.1","Local",ClasificacionEvento("Baja","<60 km"),OrigenGeneracion("Volcánico",""))
    ev3 = EventoSismico(25,"2025-05-30 12:05",UbicacionEvento((12.345,-45.678),8.9),"3.8","Local",ClasificacionEvento("Muy Baja","<30 km"),OrigenGeneracion("Artificial",""))
    app.config['analista'] = analista
    app.config['eventos'] = [ev1, ev2, ev3]
    if WEB_UI:
        app.run(debug=True)
    else:
        print("CLI mode.")

if __name__ == '__main__':
    main()
