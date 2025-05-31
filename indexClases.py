from datetime import datetime

# -------------------- Domain Model Classes --------------------

class Estado:
    def __init__(self, nombre, descripcion=""):
        self.nombre = nombre
        self.descripcion = descripcion
    
    def getNombre(self):
        return self.nombre
    
    def setNombre(self, nombre):
        self.nombre = nombre
    
    def getDescripcion(self):
        return self.descripcion
    
    def setDescripcion(self, descripcion):
        self.descripcion = descripcion
    
    def esPendienteRevision(self):
        return self.nombre == "PendienteRevision"
    
    def sosBloqueadoEnRevision(self):
        return self.nombre == "BloqueadoEnRevision"
    
    def sosRechazado(self):
        return self.nombre == "Rechazado"
    
    def __str__(self):
        return f"{self.nombre}: {self.descripcion}"

class CambioEstado:
    def __init__(self, fecha_hora_inicio, estado, fecha_hora_fin=None):
        # fecha_hora_inicio and fecha_hora_fin can be datetime or str
        self.fecha_hora_inicio = fecha_hora_inicio
        self.estado = estado          # Instance of Estado
        self.fecha_hora_fin = fecha_hora_fin

    @classmethod
    def new(cls, estado):
        return cls(datetime.now(), estado)

    def setFechaHoraFin(self, fecha):
        self.fecha_hora_fin = fecha

    def esActual(self):
        return self.fecha_hora_fin is None

    def esPendienteRevision(self):
        return self.estado.nombre == "PendienteRevision"

    def __str__(self):
        # Formatear fecha_hora_inicio, si es datetime
        try:
            ts_inicio = self.fecha_hora_inicio.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            ts_inicio = str(self.fecha_hora_inicio)
        # Formatear fecha_hora_fin, si existe y es datetime
        if self.fecha_hora_fin:
            try:
                fin = self.fecha_hora_fin.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                fin = str(self.fecha_hora_fin)
        else:
            fin = "Actual"
        return f"{self.estado.nombre} desde {ts_inicio} hasta {fin}"

class Usuario:
    def __init__(self, nombre, fechaAlta, contrasena=None):
        self.nombre = nombre
        self.fechaAlta = fechaAlta
        self.contrasena = contrasena
        self.analistaEnSismos = None  # Association to AnalistaEnSismos
    
    def getAnalistaSismos(self):
        return self.analistaEnSismos

class AnalistaEnSismos(Usuario):
    def __init__(self, nombre, mail, fechaAlta=None, contrasena=None):
        super().__init__(nombre, fechaAlta, contrasena)
        self.mail = mail
    
    def getNombre(self):
        return self.nombre

class Sesion:
    def __init__(self, fecha_hora_inicio, usuario, fecha_hora_fin=None):
        self.fecha_hora_inicio = fecha_hora_inicio
        self.usuario = usuario
        self.fecha_hora_fin = fecha_hora_fin
    
    def getUsuarioLogueado(self):
        return self.usuario

# -------------------- Seismology Domain Classes --------------------

class EstacionSismologica:
    def __init__(self, id_estacion, nombre_estacion, documento_certificacion_adq,
                 fecha_solicitud_certificacion, latitud, longitud, nro_certificacion_adq):
        self.id_estacion = id_estacion
        self.nombre_estacion = nombre_estacion
        self.documento_certificacion_adq = documento_certificacion_adq
        self.fecha_solicitud_certificacion = fecha_solicitud_certificacion
        self.latitud = latitud
        self.longitud = longitud
        self.nro_certificacion_adq = nro_certificacion_adq
    
    def clasificarMuestra(self, muestra):
        """Stub: Clasifica una muestra basada en criterios de la estación."""
        # Lógica de clasificación aquí
        pass

class Sismografo:
    def __init__(self, id_sismografo, nombre_sismografo, descripcion, nro_serie, estacion=None):
        self.id_sismografo = id_sismografo
        self.nombre_sismografo = nombre_sismografo
        self.descripcion = descripcion
        self.nro_serie = nro_serie
        self.estacion = estacion  # Instancia de EstacionSismologica
    
    def esTuMuestra(self, muestra):
        """Determina si la muestra pertenece a este sismógrafo."""
        # Lógica de validación aquí
        return True
    
    def clasificarMuestra(self, muestra):
        """Clasifica la muestra usando la lógica del sismógrafo."""
        # Lógica de clasificación específica del sismógrafo
        pass

class MagnitudRichter:
    def __init__(self, numero, descripcion, unidad):
        self.numero = numero
        self.descripcion = descripcion
        self.unidad = unidad
    
    def getNumero(self):
        return self.numero
    
    def __str__(self):
        return f"{self.numero} {self.unidad} - {self.descripcion}"

class ClasificacionSismo:
    def __init__(self, km_profundidad_desde, km_profundidad_hasta, nombre):
        self.km_profundidad_desde = km_profundidad_desde
        self.km_profundidad_hasta = km_profundidad_hasta
        self.nombre = nombre
    
    def getNombre(self):
        return self.nombre
    
    def __str__(self):
        return f"{self.nombre}: {self.km_profundidad_desde} - {self.km_profundidad_hasta} km"

class AlcanceSismo:
    def __init__(self, descripcion, nombre):
        self.descripcion = descripcion
        self.nombre = nombre
    
    def getNombre(self):
        return self.nombre
    
    def __str__(self):
        return f"{self.nombre} - {self.descripcion}"

class OrigenDeGeneracion:
    def __init__(self, nombre, descripcion=""):
        self.nombre = nombre
        self.descripcion = descripcion
    
    def getNombre(self):
        return self.nombre
    
    def __str__(self):
        return f"{self.nombre}: {self.descripcion}"

class UbicacionEvento:
    def __init__(self, epicentro, hipocentro):
        self.epicentro = epicentro    # (latitud, longitud)
        self.hipocentro = hipocentro  # Profundidad (km)
    
    def getLatitudEpicentro(self):
        return self.epicentro[0]
    
    def getLongitudEpicentro(self):
        return self.epicentro[1]
    
    def getHipocentro(self):
        return self.hipocentro
    
    def __str__(self):
        return f"Epicentro: {self.epicentro} | Hipocentro: {self.hipocentro} km"

class MuestraSismica:
    def __init__(self, fecha_hora_muestra, velocidad_onda, frecuencia_onda, longitud_onda):
        self.fecha_hora_muestra = fecha_hora_muestra
        self.velocidad_onda = velocidad_onda
        self.frecuencia_onda = frecuencia_onda
        self.longitud_onda = longitud_onda
    
    def getVelocidadOnda(self):
        return self.velocidad_onda
    
    def getFrecuenciaOnda(self):
        return self.frecuencia_onda
    
    def getLongitudOnda(self):
        return self.longitud_onda
    
    def __str__(self):
        return (f"Muestra @ {self.fecha_hora_muestra} | Velocidad: {self.velocidad_onda} | "
                f"Frecuencia: {self.frecuencia_onda} | Longitud: {self.longitud_onda}")

class SerieTemporal:
    def __init__(self, condicion_alarma, fecha_hora_registro, frecuencia_muestreo, muestras=None):
        self.condicion_alarma = condicion_alarma
        self.fecha_hora_registro = fecha_hora_registro
        self.frecuencia_muestreo = frecuencia_muestreo
        self.muestras = muestras or []  # Lista de MuestraSismica
    
    def getDatos(self):
        return self.muestras
    
    def conocerMuestras(self):
        return [str(m) for m in self.muestras]
    
    def __str__(self):
        return (f"Serie @ {self.fecha_hora_registro} | Condición Alarma: {self.condicion_alarma} | "
                f"Frecuencia Muestreo: {self.frecuencia_muestreo} Hz")

class EventoSismico:
    def __init__(self, id_evento, fecha_hora, ubicacion, magnitud: MagnitudRichter,
                 alcance: AlcanceSismo, clasificacion: ClasificacionSismo, origen: OrigenDeGeneracion):
        self.id_evento = id_evento
        self.fecha_hora = fecha_hora
        self.ubicacion = ubicacion            # Instancia de UbicacionEvento
        self.magnitud = magnitud              # Instancia de MagnitudRichter
        self.alcance = alcance                # Instancia de AlcanceSismo
        self.clasificacion = clasificacion    # Instancia de ClasificacionSismo
        self.origen = origen                  # Instancia de OrigenDeGeneracion
        self.estado = Estado("AutoDetectado", "Detectado automáticamente")
        self.cambios = []                     # Lista de CambioEstado
        self.series_temporales = []           # Lista de SerieTemporal
    
    def getAlcance(self):
        return self.alcance
    
    def getClasificacion(self):
        return self.clasificacion
    
    def getFechaHoraOcurrencia(self):
        return self.fecha_hora
    
    def getLatitudEpicentro(self):
        return self.ubicacion.getLatitudEpicentro()
    
    def getLongitudEpicentro(self):
        return self.ubicacion.getLongitudEpicentro()
    
    def getHipocentro(self):
        return self.ubicacion.getHipocentro()
    
    def getOrigen(self):
        return self.origen
    
    @classmethod
    def new(cls, id_evento, fecha_hora, ubicacion, magnitud, alcance, clasificacion, origen):
        return cls(id_evento, fecha_hora, ubicacion, magnitud, alcance, clasificacion, origen)
    
    def calcularUbicacion(self):
        """Ejemplo: podría calcular distancia a otra estación."""
        pass
    
    def conocerMagnitud(self):
        return self.magnitud.getNumero()
    
    def bloquearParaRevision(self, analista: AnalistaEnSismos):
        nuevo_estado = Estado("BloqueadoEnRevision", "Bloqueado para revisión manual")
        self.estado = nuevo_estado
        cambio = CambioEstado.new(nuevo_estado)
        self.cambios.append(cambio)
    
    def cambiarEstado(self, nuevo_estado: Estado):
        # Cerrar estado anterior
        if self.cambios and self.cambios[-1].esActual():
            self.cambios[-1].setFechaHoraFin(datetime.now())
        self.estado = nuevo_estado
        self.cambios.append(CambioEstado.new(nuevo_estado))
    
    def crearNuevoCambioEstado(self, estado: Estado):
        cambio = CambioEstado.new(estado)
        self.cambios.append(cambio)
    
    def buscarSeriesTemporales(self):
        return self.series_temporales
    
    def rechazar(self):
        nuevo_estado = Estado("Rechazado", "Rechazado por análisis")
        self.cambiarEstado(nuevo_estado)
    
    def esNoRevisado(self):
        return self.estado.nombre == "AutoDetectado"
    
    def agregarSerieTemporal(self, serie: SerieTemporal):
        self.series_temporales.append(serie)
    
    def __str__(self):
        return (f"Evento {self.id_evento} @ {self.fecha_hora} | Hipocentro: {self.getHipocentro()} km | "
                f"Magnitud: {self.conocerMagnitud()} | Estado: {self.estado.nombre}")

# -------------------- Example Usage (Main) --------------------
def main():
    # Crear algunos analistas
    analista = AnalistaEnSismos("Juan Pérez", "juan.perez@mail.com", datetime.now(), "s3cr3t")

    # Crear ubicaciones
    ubic1 = UbicacionEvento((24.123, -65.987), 10.5)
    ubic2 = UbicacionEvento((30.456, -70.123), 5.2)

    # Crear magnitudes, clasificaciones, alcances, orígenes
    mag1 = MagnitudRichter(4.2, "Leve", "Richter")
    clasif1 = ClasificacionSismo(30, 60, "Intermedio")
    alcan1 = AlcanceSismo("Detectable en varias provincias", "Medio Alcance")
    origen1 = OrigenDeGeneracion("Tectónico", "Movimiento de placas")

    # Crear eventos
    ev1 = EventoSismico(101, "2025-05-29 10:15", ubic1, mag1, alcan1, clasif1, origen1)
    ev2 = EventoSismico(102, "2025-05-30 11:20", ubic2,
                         MagnitudRichter(2.8, "Muy leve", "Richter"),
                         AlcanceSismo("Solo local", "Bajo Alcance"),
                         ClasificacionSismo(0, 30, "Superficial"),
                         OrigenDeGeneracion("Volcánico", "Erupción"))

    # Agregar serie temporal y muestras
    muestra1 = MuestraSismica("2025-05-29 10:10:00", 5.2, 1.2, 0.4)
    serie1 = SerieTemporal("Normal", "2025-05-29 10:10", 100, [muestra1])
    ev1.agregarSerieTemporal(serie1)

    # Crear estaciones y sismógrafos
    est1 = EstacionSismologica(1, "Estación Norte", "DOC123", "2025-01-15", -34.60, -58.38, "CERT456")
    sis1 = Sismografo(1, "SismoPro X", "Sismógrafo de alta precisión", "SN-001", est1)

    # Ejecutar bloqueo y cambio de estado
    print(ev1)
    ev1.bloquearParaRevision(analista)
    print(ev1)

    # Mostrar cambios de estado
    for cambio in ev1.cambios:
        print(cambio)

    # Mostrar información de serie temporal
    print(serie1)
    print(serie1.conocerMuestras())

if __name__ == '__main__':
    main()
