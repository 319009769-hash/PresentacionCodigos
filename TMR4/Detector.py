#!/usr/bin/env python3
from ev3dev2.motor import OUTPUT_D, OUTPUT_C, MoveTank
from ev3dev2.sensor.lego import UltrasonicSensor, ColorSensor
from ev3dev2.sensor import INPUT_2, INPUT_3, INPUT_4
from ev3dev2.sound import Sound
import time
import math
import sys
import io
import os
import subprocess

# --- Configuracion UTF-8 (opcional) ---
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except Exception:
    pass

# --- Inicializacion ---
sound = Sound()
tank_drive = MoveTank(OUTPUT_D, OUTPUT_C)
ultra = UltrasonicSensor(INPUT_2)
color_left = ColorSensor(INPUT_3)
color_right = ColorSensor(INPUT_4)

# --- Constantes (ajustables) ---
FORWARD_SPEED = -30          # velocidad de avance (negativa si su robot usa negativo para adelante)
SLOW_SPEED = -8              # velocidad reducida al detectar objeto cercano
ULTRA_SLOW_DISTANCE_CM = 22  # distancia en cm para empezar a reducir velocidad
BLACK_THRESHOLD = 10         # umbral de luz reflejada para detectar linea negra,
CONSECUTIVE = 1              # lecturas consecutivas requeridas (puede aumentarse si hay ruido)

# --- Funcion principal que implementa la secuencia solicitada ---
def main_sequence():
    try:
        # 1) Ejecutar la rotacion inicial exacta solicitada
        # La velocidad original es: (-30, -30, 2.87)
        tank_drive.on_for_rotations(-30, -30, 0.00)
        tank_drive.off()
        time.sleep(0.2)

        # 2) Avanzar en linea recta y reducir velocidad al detectar objeto a 10 cm
        print("Paso 2: avanzar en linea recta; reducir velocidad si objeto a <= {} cm".format(ULTRA_SLOW_DISTANCE_CM))
        left_stopped = False
        right_stopped = False
        left_count = 0
        right_count = 0

        # Empezamos avanzando a velocidad normal
        current_left_speed = FORWARD_SPEED
        current_right_speed = FORWARD_SPEED
        tank_drive.on(current_left_speed, current_right_speed)

        # Bucle principal: avanza hasta que ambos sensores de linea hayan detectado la linea negra
        while True:
            # Lectura ultrasonido
            try:
                dist = ultra.distance_centimeters
            except Exception:
                dist = None

            # Si detecta objeto a <= ULTRA_SLOW_DISTANCE_CM, reducir velocidad
            if dist is not None and dist <= ULTRA_SLOW_DISTANCE_CM:
                # reducir velocidad (si no está ya reducida)
                if current_left_speed != SLOW_SPEED or current_right_speed != SLOW_SPEED:
                    print("Objeto detectado a {:.1f} cm -> reduciendo velocidad.".format(dist))
                    current_left_speed = SLOW_SPEED
                    current_right_speed = SLOW_SPEED
                    # Si alguno de los motores ya está detenido por la linea, mantenerlo detenido
                    left_speed_to_set = 0 if left_stopped else current_left_speed
                    right_speed_to_set = 0 if right_stopped else current_right_speed
                    tank_drive.on(left_speed_to_set, right_speed_to_set)
            # Si no hay objeto cercano, mantener velocidad normal (si no se ha detenido por linea)
            else:
                if current_left_speed != FORWARD_SPEED or current_right_speed != FORWARD_SPEED:
                    current_left_speed = FORWARD_SPEED
                    current_right_speed = FORWARD_SPEED
                    left_speed_to_set = 0 if left_stopped else current_left_speed
                    right_speed_to_set = 0 if right_stopped else current_right_speed
                    tank_drive.on(left_speed_to_set, right_speed_to_set)

            # Lectura sensores de color (intensidad reflejada)
            try:
                left_val = color_left.reflected_light_intensity
            except Exception:
                left_val = None
            try:
                right_val = color_right.reflected_light_intensity
            except Exception:
                right_val = None

            # Deteccion de linea negra por cada sensor
            if left_val is not None and left_val <= BLACK_THRESHOLD:
                left_count += 1
            else:
                left_count = 0

            if right_val is not None and right_val <= BLACK_THRESHOLD:
                right_count += 1
            else:
                right_count = 0

            # Si el sensor izquierdo detecta la linea (primer sensor que la toque)
            if left_count >= CONSECUTIVE and not left_stopped:
                left_stopped = True
                # Detener solo el motor izquierdo y mantener derecho moviéndose hasta que toque
                print("Sensor izquierdo detecto linea -> detener motor izquierdo y esperar al derecho.")
                # left motor = 0, right motor = current_right_speed (si no detenido)
                tank_drive.on(0, 0 if right_stopped else current_right_speed)

            # Si el sensor derecho detecta la linea
            if right_count >= CONSECUTIVE and not right_stopped:
                right_stopped = True
                print("Sensor derecho detecto linea -> detener motor derecho y esperar al izquierdo.")
                tank_drive.on(0 if left_stopped else current_left_speed, 0)

            # Si ambos sensores ya detectaron la linea, salir
            if left_stopped and right_stopped:
                print("Ambos sensores detectaron la linea -> detener completamente.")
                tank_drive.off()
                break

            time.sleep(0.02)

        # 3) Retroceder con la instruccion solicitada: on_for_rotations(15, 15, 0.87)
        print("Paso 3: retroceder con on_for_rotations(15, 15, 0.87)")
        # Según la convencion de velocidades del usuario, 15 puede corresponder a retroceso.
        tank_drive.on_for_rotations(15, 15, 1.2)
        tank_drive.off()
        time.sleep(0.2)

        # 4) Giro de 270 grados hacia la izquierda
        print("Paso 4: giro ~270° hacia la izquierda (aprox.)")
        # Hacemos un giro en sitio: motor izquierdo hacia atrás, derecho hacia adelante.
        # El valor de 'degrees' es aproximado y puede necesitar ajuste según la geometria del robot.
        # Aqui usamos 3000 grados de motor como aproximacion para 270° de giro del robot.
        tank_drive.on_for_degrees(25, -25, 1100)
        tank_drive.off()

        print("Secuencia completada.")

    except KeyboardInterrupt:
        print("Secuencia interrumpida por teclado.")
        tank_drive.off()
    except Exception as e:
        print("Error durante la secuencia:", e)
        tank_drive.off()


if __name__ == "__main__":
    main_sequence()
    # Al terminar la secuencia, ejecutar Recolector.py en el mismo directorio
    def run_recolector():
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            recolector_path = os.path.join(script_dir, 'Recolector.py')
            if not os.path.exists(recolector_path):
                print('Recolector.py no encontrado en', recolector_path)
                return
            print('Iniciando Recolector.py...')
            subprocess.run([sys.executable, recolector_path])
        except Exception as e:
            print('Error al ejecutar Recolector.py:', e)

    run_recolector()
