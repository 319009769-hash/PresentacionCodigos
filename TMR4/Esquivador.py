#!/usr/bin/env python3
from ev3dev2.motor import OUTPUT_D, OUTPUT_C, MoveTank
from ev3dev2.sensor.lego import UltrasonicSensor, ColorSensor
from ev3dev2.sensor import INPUT_2, INPUT_3, INPUT_4
from ev3dev2.sound import Sound
import time
import sys
import io
import math

# --- Configuración de salida UTF-8 ---
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except Exception:
    pass

# --- Inicialización de objetos ---
sound = Sound()
tank_drive = MoveTank(OUTPUT_D, OUTPUT_C)
ultra = UltrasonicSensor(INPUT_2)
color_sensor_left = ColorSensor(INPUT_3)
color_sensor_right = ColorSensor(INPUT_4)

# --- Constantes ---
SPEED = -20
STOP_DISTANCE_CM = 10
WHEEL_DIAMETER_CM = 5.6
ULTRA_SLOW_DISTANCE_CM = 20
BLACK_THRESHOLD = 20
CONSECUTIVE_READINGS = 5


# --- Rutina de reposicionamiento ---
def reposicionamiento():
    normal_speed = SPEED
    reduced_speed = int(SPEED * 0.5) if SPEED != 0 else 0
    left_count = 0
    right_count = 0
    left_stopped = False
    right_stopped = False

    print("Iniciando reposicionamiento con ultrasonido y sensores de línea...")
    tank_drive.on(SPEED, SPEED)
    print("Avanzando hacia adelante durante 10 s...")
    time.sleep(10)
    tank_drive.off()
    tank_drive.on_for_degrees(-8, 25, 1010)
    tank_drive.off()
    try:
        while True:
            # Lectura ultrasonido
            try:
                dist = ultra.distance_centimeters
            except Exception:
                dist = None

            active_speed = reduced_speed if (dist is not None and dist <= ULTRA_SLOW_DISTANCE_CM) else normal_speed

            # Lectura sensores de color
            try:
                left_val = color_sensor_left.reflected_light_intensity
            except Exception:
                left_val = None
            try:
                right_val = color_sensor_right.reflected_light_intensity
            except Exception:
                right_val = None

            # Detección de línea
            if left_val is not None and left_val <= BLACK_THRESHOLD:
                left_count += 1
            else:
                left_count = 0

            if right_val is not None and right_val <= BLACK_THRESHOLD:
                right_count += 1
            else:
                right_count = 0

            if left_count >= CONSECUTIVE_READINGS and not left_stopped:
                left_stopped = True
                print("Sensor izquierdo detectó línea; motor izquierdo detenido.")

            if right_count >= CONSECUTIVE_READINGS and not right_stopped:
                right_stopped = True
                print("Sensor derecho detectó línea; motor derecho detenido.")

            left_speed = 0 if left_stopped else active_speed
            right_speed = 0 if right_stopped else active_speed

            if left_stopped and right_stopped:
                tank_drive.off()
                print("Ambos sensores detectaron la línea; reposicionamiento completado.")
                break

            tank_drive.on(left_speed, right_speed)
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Reposicionamiento interrumpido por teclado.")
    finally:
        tank_drive.off()


# --- Rutina de esquive ---
def esquive():
    print("Iniciando esquive...")
    tank_drive.on(SPEED, SPEED)

    try:
        while True:
            try:
                dist = ultra.distance_centimeters
            except Exception:
                dist = None

            if dist is None:
                time.sleep(0.05)
                continue

            print("Distancia: {:.1f} cm".format(dist))

            if dist <= STOP_DISTANCE_CM:
                tank_drive.off()
                print("Objeto detectado a {:.1f} cm — detenido.".format(dist))

                # Retroceso
                distance_back_cm = 15
                rotations = distance_back_cm / (math.pi * WHEEL_DIAMETER_CM)
                backward_speed = -SPEED
                tank_drive.on_for_rotations(backward_speed, backward_speed, rotations)
                tank_drive.off()
                print("Retrocedió aproximadamente {:.1f} cm.".format(distance_back_cm))

                # Giro izquierda
                tank_drive.on_for_degrees(15, -15, 1000)
                tank_drive.off()
                print("Giro a la izquierda de 270° completado.")

                # Avance 5 segundos
                tank_drive.on(SPEED, SPEED)
                print("Avanzando hacia adelante durante 5 s...")
                time.sleep(11)
                tank_drive.off()
                print("Avance de 5 s completado.")

                # Giro derecha
                tank_drive.on_for_degrees(-5, 40, 2200)
                tank_drive.off()
                print("Giro a la derecha de 270° completado.")

                # --- Segunda verificación con avance ---
                print("Avanzando 5 s para verificar segundo obstáculo...")
                start_time = time.time()
                tank_drive.on(SPEED, SPEED)
                second_obstacle = False

                while time.time() - start_time < 5:
                    try:
                        second_dist = ultra.distance_centimeters
                    except Exception:
                        second_dist = None

                    if second_dist is not None and second_dist <= STOP_DISTANCE_CM:
                        print("Segundo obstáculo detectado a {:.1f} cm.".format(second_dist))
                        second_obstacle = True
                        break

                    time.sleep(0.05)

                tank_drive.off()

                if second_obstacle:
                    ejecutar_segundo_esquive()
                else:
                    print("No se detectó segundo obstáculo en avance. Pasando a reposicionamiento...")
                    reposicionamiento()

                break  # salir del bucle principal

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Esquive interrumpido por teclado.")
    finally:
        tank_drive.off()


# --- Rutina de segundo esquive ---
def ejecutar_segundo_esquive():
    print("Iniciando segundo esquive...")

    # Retroceso
    distance_back_cm = 15
    rotations = distance_back_cm / (math.pi * WHEEL_DIAMETER_CM)
    backward_speed = -SPEED
    tank_drive.on_for_rotations(backward_speed, backward_speed, rotations)
    tank_drive.off()
    print("Retrocedió aproximadamente {:.1f} cm.".format(distance_back_cm))

    # Giro izquierda
    tank_drive.on_for_degrees(15, -15, 1000)
    tank_drive.off()
    print("Giro a la izquierda de 270° completado.")

    # Avance 5 segundos
    tank_drive.on(SPEED, SPEED)
    print("Avanzando hacia adelante durante 5 s...")
    time.sleep(5)
    tank_drive.off()
    print("Avance de 5 s completado.")

    # Giro derecha
    tank_drive.on_for_degrees(-0, 45, 2500)
    tank_drive.off()
    print("Giro a la derecha de 270° completado.")

    # Finalmente reposicionamiento
    reposicionamiento()


# --- Programa principal ---
def main():
    esquive()

if __name__ == "__main__":
    main()
