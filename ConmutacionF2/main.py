#!/usr/bin/env python3
from ev3dev2.motor import OUTPUT_D, OUTPUT_C, MoveTank
from ev3dev2.sensor.lego import ColorSensor
from ev3dev2.sensor import INPUT_4, INPUT_3
from ev3dev2.sound import Sound
from ev3dev2.button import Button   # ← añadido
import time
import sys
import io

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except Exception:
    pass

sound = Sound()
tank_drive = MoveTank(OUTPUT_D, OUTPUT_C)

color_sensor_left = ColorSensor(INPUT_4)
color_sensor_right = ColorSensor(INPUT_3)

Kp, Ki, Kd = 1.2, 0.0, 0.8
integral, last_error = 0, 0
base_speed = 15
calibrate_time = 2.0
calibrate_interval = 0.01

black_value, color_value, threshold = None, None, None
left_motor_inverted = True
right_motor_inverted = True

btn = Button()   # ← objeto para leer botones

def calibrar(sample_time=calibrate_time, sample_interval=calibrate_interval):
    global black_value, color_value, threshold
    # Intento usar constantes definidas en Recolector.py (p.ej. LINE_REFLECT_THRESH)
    try:
        import Recolector as reco

        # Obtener valor de linea (negro) desde Recolector si existe
        if hasattr(reco, 'LINE_REFLECT_THRESH'):
            black_value = float(reco.LINE_REFLECT_THRESH)
            print("Usando LINE_REFLECT_THRESH de Recolector como valor de linea: {:.2f}".format(black_value))
        else:
            black_value = None

        # Buscar posibles nombres para valor de fondo en Recolector
        bg_candidates = ['COLOR_FONDO', 'COLOR_BACKGROUND', 'BACKGROUND_REFLECT', 'FONDO_REFLECT', 'COLOR_VALUE', 'LINE_BG', 'FONDO', 'BACKGROUND']
        color_value = None
        for name in bg_candidates:
            if hasattr(reco, name):
                color_value = float(getattr(reco, name))
                print("Usando {} de Recolector como valor de fondo: {:.2f}".format(name, color_value))
                break

        # Si no hay valor de fondo en Recolector, muestrear el sensor izquierdo brevemente
        if color_value is None:
            print("No se encontró valor de fondo en Recolector; muestreando sensor S4 para estimar fondo...")
            sum_samples = count = 0
            start_time = time.time()
            # muestreo corto para estimar el fondo
            while time.time() - start_time < 0.5:
                sum_samples += color_sensor_left.reflected_light_intensity
                count += 1
                time.sleep(0.01)
            color_value = sum_samples / count if count else (black_value + 40 if black_value else 50)
            print("Valor fondo estimado (S4): {:.2f} ({} muestras)".format(color_value, count))

        # Si no hay valor de linea, estimar a partir del fondo o muestrear
        if black_value is None:
            if color_value is not None:
                black_value = max(0.0, color_value - 40.0)
                print("Estimando valor de linea a partir del fondo: {:.2f}".format(black_value))
            else:
                print("No se encontró valor de linea en Recolector; muestreando sensor S4 para linea...")
                sum_samples = count = 0
                start_time = time.time()
                while time.time() - start_time < sample_time:
                    sum_samples += color_sensor_left.reflected_light_intensity
                    count += 1
                    time.sleep(sample_interval)
                black_value = sum_samples / count if count else 0
                print("Valor negro promedio (S4): {:.2f} ({} muestras)".format(black_value, count))

    except Exception as e:
        # Si no se puede importar Recolector, realizar calibración automática por muestreo
        print("No se pudo usar Recolector ({}). Realizando calibración por muestreo automático.".format(e))
        print("Muestreando sensor S4 sobre la linea...")
        sum_samples = count = 0
        start_time = time.time()
        while time.time() - start_time < sample_time:
            sum_samples += color_sensor_left.reflected_light_intensity
            count += 1
            time.sleep(sample_interval)
        black_value = sum_samples / count if count else 0
        print("Valor negro promedio (S4): {:.2f} ({} muestras)".format(black_value, count))

        print("Muestreando sensor S4 sobre el fondo...")
        sum_samples = count = 0
        start_time = time.time()
        while time.time() - start_time < sample_time:
            sum_samples += color_sensor_left.reflected_light_intensity
            count += 1
            time.sleep(sample_interval)
        color_value = sum_samples / count if count else (black_value + 40 if black_value else 50)
        print("Valor colorFondo promedio (S4): {:.2f} ({} muestras)".format(color_value, count))

    threshold = (black_value + color_value) / 2 if (black_value is not None and color_value is not None) else (black_value if black_value is not None else 0)
    print("Umbral calculado: {:.2f}".format(threshold))

def rutina_salida():
    sound.beep()
    tank_drive.on_for_rotations(-15, -15, 5.87) #la primera variable es del motor izquierdo, la segunda del motor derecho y el tercer valor es de rotaciones
    tank_drive.on_for_degrees(-10, 40, 1240)
    #670
    # la linea de codigo de arriba es un giro hacia el lado derecho
    tank_drive.on_for_rotations(-20, -20, 0.70)
    tank_drive.on_for_degrees(-5, 30, 100)
    # 50 No olvidar invertir los valores
    tank_drive.on_for_rotations(-0, -30, 0.10)
    # tank_drive.on_for_rotations(15, 15, 0.80)-------------------------------------------------------
    tank_drive.on_for_degrees(-5, 30, 740)
    #tank_drive.on_for_rotations(-15, -15, 1.40)
    tank_drive.off()
    #Intentar volver a la línea antes de finalizar la rutina de salida
    Regreso_linea()
    print("Rutina de salida ejecutada!")

def Regreso_linea():
    global black_value, left_motor_inverted, right_motor_inverted, threshold
    sound.beep()
    if black_value is None or threshold is None:
        print("No hay valores de calibración; asegúrate de calibrar primero.")
        return
    print("Iniciando regreso a la línea: ligera desviación a la derecha (usando calibración)...")
    start_time = time.time()
    max_search_time = 30.0  # segundos de seguridad para no quedarse buscando indefinidamente
    detect_margin = 2
    # Avanzar con una ligera desviación a la derecha: izquierda más rápido que derecha
    left_speed = 15
    right_speed = 11

    while True:
        right_value = color_sensor_right.reflected_light_intensity
        # Usar el umbral calculado en calibrar si está disponible, si no usar black_value como fallback
        if threshold is not None:
            is_on_line = right_value <= (threshold + detect_margin)
        else:
            is_on_line = right_value <= (black_value + detect_margin)

        if is_on_line:
            tank_drive.off()
            print("Sensor derecho detectó la línea negra (valor: {:.2f}).".format(right_value))
            break
        if time.time() - start_time > max_search_time:
            tank_drive.off()
            print("Tiempo máximo de búsqueda alcanzado. Deteniéndose.")
            break
        send_left = left_speed * (-1 if left_motor_inverted else 1)
        send_right = right_speed * (-1 if right_motor_inverted else 1)
        tank_drive.on(send_left, send_right)
        time.sleep(0.05)
    time.sleep(0.2)

def rutina_seguridad():
    sound.beep()
    tank_drive.on_for_rotations(15, 15, 0.87)
    tank_drive.on_for_degrees(-15, 15, 250)
    tank_drive.on_for_rotations(15, 15, 0.80)
    tank_drive.on_for_degrees(8, -18, 1385)
    tank_drive.on_for_rotations(-15, -15, 0.57)
    #tank_drive.on_for_degrees(-15, 15, 180)
    tank_drive.on_for_rotations(-15, -15, 1.7)
    tank_drive.off()
    print("Ambos sensores detectaron negro, rutina de seguridad ejecutada!")
    # Después de la rutina de seguridad, intentar volver a la línea
    Regreso_linea()

def line_follower():
    global integral, last_error
    while True:
        left_value = color_sensor_left.reflected_light_intensity
        right_value = color_sensor_right.reflected_light_intensity

        # Detección de ambos sensores usando el umbral calculado en `calibrar`.
        detect_margin = 2
        if threshold is not None:
            left_on_line = left_value <= (threshold + detect_margin)
            right_on_line = right_value <= (threshold + detect_margin)
        else:
            # Fallback si no se calibró: usar black_value como antes
            left_on_line = (black_value is not None) and (left_value <= black_value + detect_margin)
            right_on_line = (black_value is not None) and (right_value <= black_value + detect_margin)

        if left_on_line and right_on_line:
            rutina_seguridad()
            continue

        avg_value = (left_value + right_value) / 2
        error = avg_value - threshold

        integral += error
        derivative = error - last_error
        turn = Kp * error + Ki * integral + Kd * derivative

        left_speed = max(min(base_speed + turn, 25), -25)
        right_speed = max(min(base_speed - turn, 25), -25)

        send_left = left_speed * (-1 if left_motor_inverted else 1)
        send_right = right_speed * (-1 if right_motor_inverted else 1)
        tank_drive.on(send_left, send_right)

        last_error = error
        time.sleep(0.01)

if __name__ == "__main__":
    try:
        calibrar()
        print("Calibracion lista. Presiona el boton central para comenzar...")
        sound.beep()
        # Esperar hasta que se presione el boton central
        while not btn.enter:
            time.sleep(0.1)
        print("Boton presionado, iniciando rutina salida.")
        sound.beep()
        rutina_salida()   # ← nueva rutina previa
        print("Boton presionado, iniciando seguidor de linea.")
        sound.beep()
        line_follower()
    except KeyboardInterrupt:
        tank_drive.off()
        print("Programa detenido.")

