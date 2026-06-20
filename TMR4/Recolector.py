#!/usr/bin/env python3
# Requiere ev3dev2
from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D, SpeedPercent, MoveTank
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_3, INPUT_4
from ev3dev2.button import Button
from ev3dev2.sound import Sound
import time
import math
import os
import sys
import subprocess
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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
# Velocidades
VEL_NORMAL = -10   # SpeedPercent para avance normal (reducido)
# VEL_NORMAL = -25
VEL_LENTO = -15
VEL_RAPIDO = -35

# Umbrales y tiempos
# Umbral de reflectancia para detectar línea negra (sensor izquierdo)
LINE_REFLECT_THRESH = 3
# Umbral para el sensor derecho (INPUT_4).
# Debe ser menor que el izquierdo para hacerlo menos sensible a sombras,
# pero no tan bajo que nunca llegue a detectar la línea. Ajuste para pruebas.
LINE_REFLECT_THRESH_DER = 0
DIST_THRESH_CM = 3.0 # 
STOP_DIST_CM = 1.0
TIEMPO_ESPERA_SENSOR = 2.0  # segundos para esperar deteccion de objeto
RGB_LIMITE = 20              # umbral de reflexion para detectar objeto en garra
# Deteccion de cruce: ventana temporal para permitir deteccion casi-simultanea
CROSS_DETECT_WINDOW_S = 0.4  # segundos

# Lectura de color: ahora más tiempo para decidir
VERDE_REPETICIONES = 10     # antes 5 -> ahora 10 muestras
MUESTRA_DELAY_S = 0.5       # retardo entre muestras (segundos), antes 0.25

# Debounce corto para detección del sensor derecho durante muestreos
RIGHT_LINE_DEBOUNCE_READS = 3
RIGHT_LINE_DEBOUNCE_INTERVAL_S = 0.05

# Habilitar debug de sensores para pruebas (cambiar a False tras verificar)
DEBUG_SENSOR = True

# Alturas (parametrizadas en cm)
ALTO_CM = 4.6
MEDIO_CM = 0.0
#MEDIO_CM = 12.0
BAJO_CM = 20.6

# Garras (power/time)
GARRA_POWER = 70   # porcentaje de potencia para run_timed
GARRA_TIME_S = 2.5 # segundos para abrir/cerrar (aprox)

# Elevador: diametro tambor en mm (para convertir cm a grados)
ELEVADOR_DIAM_TAMBOR_MM = 24.0

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

        # Estado para intercalar alturas: empieza en MEDIO
        self.next_altura = MEDIO_CM

        # Bandera para controlar el primer cruce de linea negra
        self.first_cross = False

        # Parámetros y estado del controlador PID para el seguidor de línea
        # (valores tomados/adaptados de SeguidorDeLineas.py)
        self.kp = 1.2
        self.ki = 0.0
        self.kd = 0.8
        self.integral = 0.0
        self.last_error = 0.0
        # Usamos la velocidad base definida en las constantes
        self.base_speed = VEL_NORMAL

        # >>> Correccion: llevar elevador a MEDIO desde el inicio <<<
        # Esto asegura que las lecturas comiencen desde la altura deseada.
        try:
            self.elev.ir_altura_cm(MEDIO_CM)
            time.sleep(0.2)  # pequeña pausa para estabilizar
        except Exception:
            # Si falla, continuar pero advertir por consola
            print("Advertencia: no se pudo mover elevador a MEDIO al iniciar.")

    def seguir_linea_step(self):
        """
        Seguidor de línea basado en PID usando el sensor izquierdo
        (adaptado desde SeguidorDeLineas.py). Calcula un giro `turn`
        a partir del error entre el umbral de línea y la lectura y aplica
        velocidades diferenciales al `MoveTank`.
        """
        try:
            light = self.line_izq.reflected_light_intensity
        except Exception as e:
            if DEBUG_SENSOR:
                print("seguir_linea_step: error leyendo sensor izquierdo:", e)
            # Si falla la lectura, usar umbral como lectura segura
            light = LINE_REFLECT_THRESH

        # Error: target - measured (convención igual a SeguidorDeLineas.py)
        error = LINE_REFLECT_THRESH - light

        # PID
        self.integral += error
        derivative = error - self.last_error
        turn = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)

        base = self.base_speed
        left_speed = max(min(base + turn, 100), -100)
        right_speed = max(min(base - turn, 100), -100)

        if DEBUG_SENSOR:
            print("Seguidor PID: light=", light, "error=", error, "turn=", turn,
                  "left=", left_speed, "right=", right_speed)

        self.tank.on(SpeedPercent(left_speed), SpeedPercent(right_speed))

        # Guardar para la siguiente iteración
        self.last_error = error

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
        # Mientras se toman muestras, monitorizamos el sensor derecho por si encuentra la linea negra
        muestras = []
        verde_count = 0
        no_verde_count = 0
        last_rgb = (0,0,0)
        start_m = time.time()
        for _ in range(VERDE_REPETICIONES):
            # Tomar muestra
            r, g, b = self.color_garra.rgb
            muestras.append((r, g, b))
            last_rgb = (r, g, b)
            if es_verde_rgb(r, g, b):
                verde_count += 1
                self.sound.beep()
            else:
                no_verde_count += 1

            # Chequear sensor derecho de linea durante la toma de muestras (con debounce)
            try:
                de_ref = self.line_der.reflected_light_intensity
                if de_ref < LINE_REFLECT_THRESH_DER:
                    # confirmar con debounce corto antes de lanzar
                    if self.confirmar_linea_derecha():
                        print("Sensor derecho detectó línea durante muestreo -> lanzando RecolectorRevers")
                        self.lanzar_recolector_revers()
            except Exception:
                pass

            time.sleep(MUESTRA_DELAY_S)

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
    def lanzar_recolector_revers(self):
        """
        Lanza el script RecolectorRevers.py y termina el proceso actual.
        """
        try:
            script_path = os.path.join(os.path.dirname(__file__), "RecolectorRevers.py")
            print("Lanzando RecolectorRevers:", script_path)
            # Detener motores antes de cambiar de modo
            self.tank.off()
            subprocess.Popen([sys.executable, script_path])
            # Salir del proceso actual para ceder al modo reversa
            sys.exit(0)
        except Exception as e:
            print("Error al lanzar RecolectorRevers.py:", e)
    def confirmar_linea_derecha(self, reads=RIGHT_LINE_DEBOUNCE_READS, interval=RIGHT_LINE_DEBOUNCE_INTERVAL_S):
        """Confirma con debounce que el sensor derecho detecta la línea negra."""
        try:
            for i in range(reads):
                val = self.line_der.reflected_light_intensity
                if DEBUG_SENSOR:
                    print("confirmar_linea_derecha: read", i+1, "of", reads, "val=", val, "thresh=", LINE_REFLECT_THRESH_DER)
                if val >= LINE_REFLECT_THRESH_DER:
                    if DEBUG_SENSOR:
                        print("confirmar_linea_derecha: not confirmed (value >= thresh)")
                    return False
                time.sleep(interval)
            if DEBUG_SENSOR:
                print("confirmar_linea_derecha: confirmed (all reads below thresh)")
            return True
        except Exception as e:
            if DEBUG_SENSOR:
                print("confirmar_linea_derecha: exception:", e)
            return False

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
            de_line = self.line_der.reflected_light_intensity < LINE_REFLECT_THRESH_DER
            if iz_line and de_line:
                self.tank.off()
                self.sound.beep()
                print("Cruce de linea detectado: ambos sensores en negro")
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
        hasta que ambos sensores de linea detecten negro simultáneamente por segunda vez
        o se presione el boton.
        """
        print("Iniciando busqueda en ALTURA MEDIA. Presiona boton para detener.")
        # Asegurar que la siguiente altura sea MEDIO
        self.next_altura = MEDIO_CM


        # Variables para deteccion con ventana temporal
        t_iz = None
        t_de = None
        window = CROSS_DETECT_WINDOW_S

        while not self.btn.any():
            now = time.time()
            iz_val = self.line_izq.reflected_light_intensity
            de_val = self.line_der.reflected_light_intensity
            iz_line = iz_val < LINE_REFLECT_THRESH
            de_line = de_val < LINE_REFLECT_THRESH_DER

            if DEBUG_SENSOR:
                print("Reflect:", "iz=", iz_val, "de=", de_val, "iz_line=", iz_line, "de_line=", de_line)

            # Si el sensor izquierdo encuentra línea negra, finalizar el programa inmediatamente.
            if iz_line:
                print("Sensor izquierdo detectó línea negra. Finalizando programa.")
                self.tank.off()
                return True

            # Si ambos sensores detectan negro en el mismo muestreo, detiene ya
            if iz_line and de_line:
                print("Cruce de linea detectado (sensores 3 y 4, mismo muestreo). Finalizando busqueda.")
                self.tank.off()
                return True

            # Registrar cuando cada sensor detecta negro por primera vez
            if iz_line:
                if t_iz is None:
                    t_iz = now
            else:
                # Limpiar timestamp si expiró la ventana
                if t_iz is not None and (now - t_iz) > window:
                    t_iz = None

            if de_line:
                if t_de is None:
                    t_de = now
            else:
                if t_de is not None and (now - t_de) > window:
                    t_de = None

            # Si ambos detectaron dentro de la ventana permitida, considerar simultaneo
            if t_iz is not None and t_de is not None and abs(t_iz - t_de) <= window:
                print("Cruce de linea detectado (sensores 3 y 4, ventana temporal). Finalizando busqueda.")
                self.tank.off()
                return True

            # Seguir linea y buscar objetos
            self.seguir_linea_step()

            if self.detectar_objeto_garra():
                self.tank.off()
                print("Objeto detectado en garra -> ejecutar recoleccion en MEDIO")
                # Ejecutar recoleccion en MEDIO sin intercalar y sin esperar al cruce
                # (el bucle principal de busqueda detectará el cruce automáticamente)
                self.rutina_recoleccion(MEDIO_CM, allow_intercalar=False, esperar_cruce=False)

                # Asegurar elevador vuelva a MEDIO antes de continuar
                try:
                    self.elev.ir_altura_cm(MEDIO_CM)
                    time.sleep(0.2)
                except Exception:
                    print("Advertencia: no se pudo mover elevador a MEDIO al reanudar.")

                print("Reanudando busqueda en MEDIO")

            time.sleep(0.02)

        return False

    def run(self):
        print("Iniciando modo: busqueda en ALTURA MEDIA. Presiona boton para detener.")
        finished = False
        try:
            # Ejecutar busqueda repetida en MEDIO hasta el segundo cruce de línea (sensores 3 y 4)
            finished = self.buscar_pelotas_en_medio()
        except KeyboardInterrupt:
            pass
        finally:
            self.tank.off()
            print("Programa finalizado")
'''
        # Si la busqueda terminó por detección de las dos líneas negras, lanzar RecolectorRevers.py
        if finished:
            try:
                script_path = os.path.join(os.path.dirname(__file__), "RecolectorRevers.py")
                print("Lanzando:", script_path)
                # Ejecutar como proceso hijo y salir del proceso actual
                subprocess.Popen([sys.executable, script_path])
                sys.exit(0)
            except Exception as e:
                print("Error al lanzar RecolectorRevers.py:", e)
'''
# -----------------------
# Ejecutable
# -----------------------
if __name__ == "__main__":
    robot = LineFollowerRobot()
    robot.run()
