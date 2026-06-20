#!/usr/bin/env python3
# Requiere ev3dev2
from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D, SpeedPercent, MoveTank
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_3, INPUT_4
from ev3dev2.button import Button
from ev3dev2.sound import Sound
import time
import math

# -----------------------
# Configuracion de pines
# -----------------------
PIN_GARRA = OUTPUT_A      # Motor medio o grande para garra
PIN_ELEVADOR = OUTPUT_B   # Motor para elevador (tambor)
PIN_DER = OUTPUT_C        # Motor derecho tren motriz
PIN_IZQ = OUTPUT_D        # Motor izquierdo tren motriz

SENSOR_GARRA = INPUT_1    # Sensor de color en la garra (deteccion/reflexion/RGB)
SENSOR_LINEA_IZQ = INPUT_3
SENSOR_LINEA_DER = INPUT_4
SENSOR_ULTRA = INPUT_2

# -----------------------
# Parametros (personalizables)
# -----------------------
# Velocidades (negativas para marcha atrás)
VEL_NORMAL = -25   # SpeedPercent para avance normal (reducido, reversa)
VEL_LENTO = -15
VEL_RAPIDO = -35

# Umbrales y tiempos
LINE_REFLECT_THRESH = 4
DIST_THRESH_CM = 3.0
STOP_DIST_CM = 1.0
TIEMPO_ESPERA_SENSOR = 2.0  # segundos para esperar deteccion de objeto
RGB_LIMITE = 20              # umbral de reflexion para detectar objeto en garra

# Lectura de color: ahora más tiempo para decidir
VERDE_REPETICIONES = 10     # antes 5 -> ahora 10 muestras
MUESTRA_DELAY_S = 0.5       # retardo entre muestras (segundos), antes 0.25

# Alturas (parametrizadas en cm)
ALTO_CM = 4.6
MEDIO_CM = 4.6
#MEDIO_CM = 12.2
BAJO_CM = 20.6

# Garras (power/time)
GARRA_POWER = 70   # porcentaje de potencia para run_timed
GARRA_TIME_S = 2.5 # segundos para abrir/cerrar (aprox)

# Elevador: diametro tambor en mm (para convertir cm a grados)
ELEVADOR_DIAM_TAMBOR_MM = 24.0

# Inicio: configurar direccion y sensor de inicio
START_REVERSE = True  # CHANGED: iniciar movimiento en reversa si True
START_SENSOR = 4      # CHANGED: sensor de linea preferido para inicio/termino (INPUT_4)

# -----------------------
# Utilidades
def cm_a_grados(dist_cm, diam_mm):
    # 360 grados por vuelta; circunferencia = pi * diam_mm
    vueltas = (dist_cm * 10.0) / (math.pi * diam_mm)
    return int(round(360.0 * vueltas))

# -----------------------
# Deteccion de color verde (mismo enfoque: diferencias y ratios)
# -----------------------
def es_verde_rgb(r, g, b):
    """
    Reglas adaptadas del codigo original:
    - b > g > r esperado
    - diferencias y ratios en rangos especificos
    - evitar colores muy oscuros
    """
    # Asegurar enteros
    r = int(r); g = int(g); b = int(b)

    # Regla basica de orden
    if not (b > g > r):
        return False

    diff_gr = g - r
    diff_bg = b - g
    diff_br = b - r
    # Rangos por diferencias (copiados / adaptados)
    if not (24 <= diff_gr <= 36):
        return False
    if not (8 <= diff_bg <= 18):
        return False
    if not (34 <= diff_br <= 55):
        return False

    # Ratios
    ratio_gr = g / max(r, 1)
    ratio_bg = b / max(g, 1)
    if not (3.0 <= ratio_gr <= 6.0):
        return False
    if not (1.1 <= ratio_bg <= 1.7):
        return False

    # Evitar falsos verdes en colores muy oscuros
    if (r + g + b) < 50:
        return False

    return True

# -----------------------
# Clases hardware
# -----------------------
class Elevador:
    def __init__(self, motor_port, diam_tambor_mm=ELEVADOR_DIAM_TAMBOR_MM, vel=20):
        self.motor = LargeMotor(motor_port)
        self.diam = diam_tambor_mm
        self.vel = vel
        # Guardar origen en la posicion actual
        try:
            self.motor.reset()
        except Exception:
            pass
        self.pos_origen = 0

    def ir_altura_cm(self, altura_cm):
        grados = cm_a_grados(altura_cm, self.diam)
        # Ejecutar movimiento a target
        try:
            # on_to_position espera velocidad y posicion absoluta en grados
            self.motor.on_to_position(SpeedPercent(self.vel), grados)
        except Exception:
            # fallback: movimiento por tiempo (menos preciso)
            self.motor.on(SpeedPercent(self.vel))
            time.sleep(0.5)
            self.motor.off()

    def volver_a_origen(self):
        try:
            self.motor.on_to_position(SpeedPercent(self.vel), self.pos_origen)
        except Exception:
            self.motor.on(SpeedPercent(self.vel))
            time.sleep(0.5)
            self.motor.off()

class Garra:
    def __init__(self, motor_port):
        self.motor = MediumMotor(motor_port)
        self.sound = Sound()

    def cerrar(self):
        # Cerrar garra: potencia negativa (ajusta segun montaje)
        self.motor.on_for_seconds(SpeedPercent(-GARRA_POWER), GARRA_TIME_S, block=True)

    def abrir(self):
        # Abrir garra: potencia positiva
        self.motor.on_for_seconds(SpeedPercent(GARRA_POWER), GARRA_TIME_S, block=True)

# -----------------------
# Robot principal
# -----------------------
class LineFollowerRobot:
    def __init__(self):
        # Motores
        self.tank = MoveTank(PIN_IZQ, PIN_DER)
        self.elev = Elevador(PIN_ELEVADOR)
        self.garra = Garra(PIN_GARRA)

        # Sensores
        self.color_garra = ColorSensor(SENSOR_GARRA)
        self.line_izq = ColorSensor(SENSOR_LINEA_IZQ)
        self.line_der = ColorSensor(SENSOR_LINEA_DER)
        self.ultra = UltrasonicSensor(SENSOR_ULTRA)

        # Estado
        self.sound = Sound()
        self.btn = Button()

        # Configuracion de direccion y sensor de inicio
        self.reversa = START_REVERSE  # CHANGED: flag para conducir en reversa al iniciar
        # CHANGED: sensor de inicio preferido (cuando START_SENSOR==4 usamos sensor derecho)
        self.start_sensor = 'der' if START_SENSOR == 4 else 'izq'

        # Estado para intercalar alturas: empieza en ALTO (modo reversa)
        self.next_altura = ALTO_CM

        # Llevar elevador a ALTO desde el inicio
        try:
            self.elev.ir_altura_cm(ALTO_CM)
            time.sleep(0.2)  # pequeña pausa para estabilizar
        except Exception:
            # Si falla, continuar pero advertir por consola
            print("Advertencia: no se pudo mover elevador a ALTO al iniciar.")

    def seguir_linea_step(self):
        """
        Simple seguidor diferencial proporcional:
        Lee reflectancia de ambos sensores y ajusta velocidades.
        """
        iz = self.line_izq.reflected_light_intensity
        de = self.line_der.reflected_light_intensity

        Kp = 0.8

        # CHANGED: soporta modo reversa; cuando `self.reversa` es True
        # usamos el sensor derecho (4) como referencia y aplicamos base positiva.
        if getattr(self, 'reversa', False):
            # Cuando vamos en reversa, favorecemos el sensor derecho (sensor 4)
            error = de - iz  # CHANGED: usar sensor 4 como principal
            base = abs(VEL_NORMAL)  # CHANGED: base positiva para avanzar marcha atrás
        else:
            error = iz - de
            base = VEL_NORMAL

        turn = Kp * error

        # Calcular velocidades asegurando rango [-100,100]
        left_speed = max(min(int(base + turn), 100), -100)
        right_speed = max(min(int(base - turn), 100), -100)

        self.tank.on(SpeedPercent(left_speed), SpeedPercent(right_speed))

    def detectar_objeto_garra(self):
        # Usamos reflexion del sensor de la garra para detectar objeto
        reflejo = self.color_garra.reflected_light_intensity
        return reflejo > RGB_LIMITE

    def tomar_muestras_rgb(self, n=VERDE_REPETICIONES, delay=MUESTRA_DELAY_S):
        muestras = []
        for _ in range(n):
            r, g, b = self.color_garra.rgb
            muestras.append((r, g, b))
            time.sleep(delay)
        return muestras

    def decidir_color(self, muestras):
        verde_count = 0
        no_verde_count = 0
        last_rgb = (0,0,0)
        for (r,g,b) in muestras:
            last_rgb = (r,g,b)
            if es_verde_rgb(r, g, b):
                verde_count += 1
                self.sound.beep()
            else:
                no_verde_count += 1
        return verde_count, no_verde_count, last_rgb

    def rutina_recoleccion(self, altura_inicial_cm, allow_intercalar=True, esperar_cruce=True):
        # Llevar elevador a altura inicial (asegura posicion antes de leer)
        self.elev.ir_altura_cm(altura_inicial_cm)
        tiempo_inicio = time.time()
        objeto_detectado = False

        # Esperar deteccion breve (mientras el elevador ya está en la altura deseada)
        while time.time() - tiempo_inicio < TIEMPO_ESPERA_SENSOR:
            if self.detectar_objeto_garra():
                objeto_detectado = True
                break
            time.sleep(0.05)

        if not objeto_detectado:
            # No hay objeto: ajustar elevador segun logica original
            # ALTO deshabilitado: mantener MEDIO cuando se esperaba MEDIO
            if abs(altura_inicial_cm - MEDIO_CM) < 0.01:
                self.elev.ir_altura_cm(MEDIO_CM)
                time.sleep(0.2)
            else:
                self.elev.ir_altura_cm(BAJO_CM)
            return

        # Si hay objeto, tomar muestras RGB (ahora más muestras y más tiempo)
        muestras = self.tomar_muestras_rgb()
        verde_count, no_verde_count, last_rgb = self.decidir_color(muestras)

        r,g,b = last_rgb
        print("Verde detectado", verde_count, "veces; no verde", no_verde_count, "veces")
        print("RGB final:", r, g, b)

        if verde_count > no_verde_count:
            # Ignorar objeto verde: mantener elevador y seguir
            self.sound.beep()
            # ALTO deshabilitado: mantener MEDIO cuando se esperaba MEDIO
            if abs(altura_inicial_cm - MEDIO_CM) < 0.01:
                self.elev.ir_altura_cm(MEDIO_CM)
                time.sleep(0.2)
            else:
                self.elev.ir_altura_cm(BAJO_CM)
            return
        else:
            # No es verde: ejecutar rutina completa de agarre
            print("Objeto NO verde -> recoger")
            # Cerrar garra para asegurar el objeto
            self.garra.cerrar()
            time.sleep(0.1)

            # Subir el elevador a la altura MEDIA para transportar con seguridad
            try:
                self.elev.ir_altura_cm(MEDIO_CM)
                time.sleep(0.3)
            except Exception:
                print("Advertencia: no se pudo mover elevador a MEDIO tras agarrar.")

            # Confirmar que el objeto sigue presente en la garra
            if self.detectar_objeto_garra():
                print("Objeto confirmado en garra tras subir a MEDIO")
            else:
                print("Advertencia: objeto NO detectado en garra tras subir a MEDIO")

            # Regresar elevador a origen y soltar
            try:
                self.elev.volver_a_origen()
            except Exception:
                print("Advertencia: fallo al regresar elevador a origen")
            time.sleep(0.25)
            self.garra.abrir()
            time.sleep(0.1)
            print("Recoleccion completada")

            # Esperar hasta que ambos sensores detecten la linea negra simultaneamente
            # (solo si se especifica esperar_cruce=True)
            if esperar_cruce:
                self.esperar_hasta_linea_negra()

            # Si se permite intercalar, después de depositar subimos a la siguiente altura
            # y ejecutamos una recoleccion adicional en esa altura (sin volver a intercalar).
            if allow_intercalar:
                # intercalar_recoleccion se encarga de mover a self.next_altura y llamar rutina_recoleccion
                self.intercalar_recoleccion()

    def intercalar_recoleccion(self):
        """
        Mueve el elevador a la siguiente altura (self.next_altura),
        ejecuta una recoleccion en esa altura sin volver a intercalar,
        y alterna self.next_altura para la proxima vez.
        """
        # Intercalado ALTO deshabilitado: usar solo MEDIO
        print("Intercalado deshabilitado: usando solo MEDIO")
        self.next_altura = MEDIO_CM

    def esperar_hasta_linea_negra(self, timeout=10.0):
        """
        Mueve siguiendo la linea hasta que ambos sensores detecten negro
        simultáneamente o hasta agotar el timeout (segundos).
        Devuelve True si encontro la linea, False si timeout.
        """
        inicio = time.time()
        print("Buscando cruce: esperando ambos sensores en negro...")
        while time.time() - inicio < timeout:
            iz_line = self.line_izq.reflected_light_intensity < LINE_REFLECT_THRESH
            de_line = self.line_der.reflected_light_intensity < LINE_REFLECT_THRESH
            # Si ambos sensores detectan negro, detener inmediatamente
            if iz_line and de_line:
                self.tank.off()
                self.sound.beep()
                print("Cruce de linea detectado: sensores 3 y 4 en negro -> deteniendo")
                return True
            # Seguir linea mientras buscamos el cruce
            self.seguir_linea_step()
            time.sleep(0.02)
        # Timeout
        self.tank.off()
        print("Timeout esperando cruce de linea")
        return False

    def buscar_pelotas_en_medio(self):
        """
        Bucle principal de busqueda en ALTURA MEDIA.
        Repite la busqueda y recoleccion en `MEDIO` indefinidamente
        hasta que ambos sensores de linea detecten negro simultáneamente
        o se presione el boton.
        """
        # CHANGED: imprimir mensaje según modo reversa
        if getattr(self, 'reversa', False):
            print("Iniciando busqueda en ALTURA ALTO (reversa). Presiona boton para detener.")
        else:
            print("Iniciando busqueda en ALTURA ALTO (adelante). Presiona boton para detener.")
        # Asegurar que la siguiente altura sea ALTO
        self.next_altura = ALTO_CM

        while not self.btn.any():
            iz_line = self.line_izq.reflected_light_intensity < LINE_REFLECT_THRESH
            de_line = self.line_der.reflected_light_intensity < LINE_REFLECT_THRESH

            # CHANGED: usar sensor 4 (derecho / INPUT_4) como disparador de fin de busqueda
            if de_line:
                print("Cruce de linea detectado (sensor 4). Finalizando busqueda.")
                self.tank.off()
                return True

            # Seguir linea en reversa y buscar objetos
            self.seguir_linea_step()

            if self.detectar_objeto_garra():
                # Detener para evaluar objeto
                self.tank.off()
                print("Objeto detectado en garra -> ejecutar recoleccion en ALTO")
                # Ejecutar recoleccion en ALTO sin intercalar y sin esperar al cruce
                self.rutina_recoleccion(ALTO_CM, allow_intercalar=False, esperar_cruce=False)

                # Asegurar elevador vuelva a ALTO antes de continuar
                try:
                    self.elev.ir_altura_cm(ALTO_CM)
                    time.sleep(0.2)
                except Exception:
                    print("Advertencia: no se pudo mover elevador a ALTO al reanudar.")

                print("Reanudando busqueda en ALTO")

            time.sleep(0.02)

        return False

    def run(self):
        print("Iniciando modo: busqueda en ALTURA MEDIA. Presiona boton para detener.")
        try:
            # Ejecutar busqueda repetida en MEDIO hasta cruce de línea (sensores 3 y 4)
            self.buscar_pelotas_en_medio()
        except KeyboardInterrupt:
            pass
        finally:
            self.tank.off()
            print("Programa finalizado")

# -----------------------
# Ejecutable
# -----------------------
if __name__ == "__main__":
    robot = LineFollowerRobot()
    robot.run()
