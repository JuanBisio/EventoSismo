from datetime import datetime
from indexClases import (
    EventoSismico, UbicacionEvento, MagnitudRichter, AlcanceSismo,
    ClasificacionSismo, OrigenDeGeneracion, MuestraSismica, SerieTemporal,
    EstacionSismologica, Sismografo, Estado, CambioEstado, Usuario, AnalistaEnSismos
)

# Gestor que implementa el caso de uso "Registrar resultado de revisión manual"
class GestorRegistrarResultado:
    def __init__(self, eventos_db, estaciones_db, sismografos_db, usuario_logueado: AnalistaEnSismos):
        # Simula bases de datos en memoria:
        # eventos_db: lista de EventoSismico
        # estaciones_db: lista de EstacionSismologica
        # sismografos_db: lista de Sismografo
        self.eventos_db = eventos_db
        self.estaciones_db = estaciones_db
        self.sismografos_db = sismografos_db
        self.usuario = usuario_logueado

    def obtenerEventosNoRevisados(self):
        # Flujo A2: si no hay eventos no revisados, devuelve lista vacía
        return [ev for ev in self.eventos_db if ev.esNoRevisado()]

    def seleccionarEvento(self, id_evento) -> EventoSismico:
        # Encuentra el evento en la lista por ID
        for ev in self.eventos_db:
            if ev.id_evento == id_evento:
                # Bloquear para revisión (flujo principal paso 8)
                ev.bloquearParaRevision(self.usuario)
                return ev
        raise ValueError(f"Evento con id {id_evento} no encontrado")

    def obtenerDatosSismicos(self, evento: EventoSismico):
        # Paso 9: obtener alcance, clasificación, origen
        alcance = evento.getAlcance()
        clasificacion = evento.getClasificacion()
        origen = evento.getOrigen()

        # Recorrer series temporales (9.2)
        series = evento.buscarSeriesTemporales()
        datos_series = []
        for serie in series:
            muestras_str = serie.conocerMuestras()
            datos_series.append({
                "serie": serie,
                "muestras": serie.getDatos(),
                "muestras_format": muestras_str
            })

        # Flujo 9.3: llamar a GenerarSismograma (aquí stubeamos la llamada)
        # Generar un sismograma por estación: simulamos retorno de URL o ruta
        sismogramas = self._generarSismogramas(evento)

        return {
            "alcance": alcance,
            "clasificacion": clasificacion,
            "origen": origen,
            "series": datos_series,
            "sismogramas": sismogramas
        }

    def _generarSismogramas(self, evento: EventoSismico):
        # Lógica stub para GenerarSismograma: retorna un diccionario {id_estacion: "ruta_imagen"}
        resultado = {}
        for est in self.estaciones_db:
            # Por cada estación, se asume que se genera un archivo de imagen
            ruta = f"sismo_{evento.id_evento}_estacion_{est.id_estacion}.png"
            resultado[est.id_estacion] = ruta
        return resultado

    def permitirModificacionDatos(self, evento: EventoSismico, nueva_magnitud=None, nuevo_alcance=None, nuevo_origen=None):
        # Paso 12: permite modificar datos de magnitud, alcance y origen
        if nueva_magnitud:
            evento.magnitud = nueva_magnitud
        if nuevo_alcance:
            evento.alcance = nuevo_alcance
        if nuevo_origen:
            evento.origen = nuevo_origen
        # Flujo A2: si AS modifica

    def registrarAccion(self, evento: EventoSismico, accion: str):
        # Paso 14: valida que haya magnitud, alcance y origen (paso 16)
        if evento.magnitud is None or evento.alcance is None or evento.origen is None:
            raise ValueError("Faltan datos mínimos: magnitud, alcance u origen")
        if accion not in ["Confirmar", "Rechazar", "SolicitarExperto"]:
            raise ValueError("Acción inválida")

        # Paso 17 y flujos alternativos 6 y 7
        if accion == "Confirmar":
            nuevo_estado = Estado("Confirmado", "Confirmado por análisis manual")
            evento.cambiarEstado(nuevo_estado)
        elif accion == "Rechazar":
            evento.rechazar()
        elif accion == "SolicitarExperto":
            nuevo_estado = Estado("DerivadoAExperto", "Derivado a experto para revisión")
            evento.cambiarEstado(nuevo_estado)
        # Registrar quién y cuándo: en el registro de CambioEstado ya queda la fecha, se puede asociar analista si se extiende la clase CambioEstado.

    # Flujo alternativo A8: cancelar operación
    def cancelar(self, evento: EventoSismico):
        # Se puede revertir bloqueo? Podríamos cerrar el cambio de estado actual
        # Encontrar último cambio abierto
        if evento.cambios and evento.cambios[-1].esActual():
            evento.cambios[-1].setFechaHoraFin(datetime.now())
        # Volver al estado anterior o dejar como AutoDetectado
        evento.estado = Estado("AutoDetectado", "Revertido a no revisado")


# Ejemplo de configuración inicial y flujo de uso
if __name__ == "__main__":
    # Simular BD en memoria
    eventos = []
    estaciones = []
    sismografos = []

    # 1) Crear un analista que realizará la revisión
    analista = AnalistaEnSismos("Ana Gómez", "ana.gomez@mail.com", datetime.now(), "pwd123")

    # 2) Crear estaciones y sismógrafos
    est1 = EstacionSismologica(1, "Estación Norte", "DOC123", "2025-01-15", -34.60, -58.38, "CERT456")
    est2 = EstacionSismologica(2, "Estación Sur", "DOC789", "2025-02-10", -32.15, -64.50, "CERT999")
    estaciones.extend([est1, est2])
    sis1 = Sismografo(1, "SismoPro X", "Alta precisión", "SN-001", est1)
    sis2 = Sismografo(2, "SismoLite", "Baja precisión", "SN-002", est2)
    sismografos.extend([sis1, sis2])

    # 3) Crear algunos eventos sísmicos (no revisados)
    ubicA = UbicacionEvento((24.123, -65.987), 10.5)
    magA = MagnitudRichter(4.2, "Leve", "Richter")
    clasA = ClasificacionSismo(30, 60, "Intermedio")
    alcA = AlcanceSismo("Detectable en varias provincias", "Medio Alcance")
    oriA = OrigenDeGeneracion("Tectónico", "Movimiento de placas")
    evA = EventoSismico(101, "2025-05-29 10:15", ubicA, magA, alcA, clasA, oriA)
    
    # Agregar series temporales y muestras
    m1 = MuestraSismica("2025-05-29 10:10:00", 5.2, 1.2, 0.4)
    serieA = SerieTemporal("Normal", "2025-05-29 10:10", 100, [m1])
    evA.agregarSerieTemporal(serieA)
    eventos.append(evA)

    # 4) Inicializar Gestor con las "BD" y el analista
    gestor = GestorRegistrarResultado(eventos, estaciones, sismografos, analista)

    # 5) Flujo principal: obtener eventos no revisados
    sin_revisar = gestor.obtenerEventosNoRevisados()
    print("Eventos no revisados:")
    for e in sin_revisar:
        print(f"- ID: {e.id_evento}, Fecha: {e.getFechaHoraOcurrencia()}, Estado: {e.estado.nombre}")

    # 6) El analista selecciona un evento (ID 101)
    evento_sel = gestor.seleccionarEvento(101)
    print(f"\nEvento seleccionado y bloqueado: {evento_sel.id_evento}, Estado actual: {evento_sel.estado.nombre}")

    # 7) Obtener datos sísmicos para ese evento
    datos = gestor.obtenerDatosSismicos(evento_sel)
    print("\nDatos del Evento:")
    print(f"Alcance: {datos['alcance']}")
    print(f"Clasificación: {datos['clasificacion']}")
    print(f"Origen: {datos['origen']}")
    print("Series temporales y muestras:")
    for ds in datos['series']:
        print(f"  Serie: {ds['serie']}")
        for m in ds['muestras']:
            print(f"    Muestra: {m}")
    print("Sismogramas generados por estación:")
    for id_est, ruta in datos['sismogramas'].items():
        print(f"  Estación {id_est}: {ruta}")

    # 8) El analista decide no modificar datos y elige "Rechazar"
    gestor.registrarAccion(evento_sel, "Rechazar")
    print(f"\nDespués de rechazar, Estado evento: {evento_sel.estado.nombre}")
    print("Historial de Cambios de Estado:")
    for c in evento_sel.cambios:
        print(f"- {c}")