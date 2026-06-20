#!/usr/bin/env python3
from ev3dev2.motor import OUTPUT_C, OUTPUT_D, MoveTank
from ev3dev2.sensor.lego import ColorSensor
from ev3dev2.sensor import INPUT_4
import time

# Motores
tank_drive = MoveTank(OUTPUT_D, OUTPUT_C)  # D = izquierdo, C = derecho

# Sensor de color (seguimiento de línea)
color_sensor = ColorSensor(INPUT_4)

# Parámetros PID
Kp = 1.2
Ki = 0.0
Kd = 0.8

# Variables PID
integral = 0
last_error = 0

# Velocidad base
base_speed = 20

# Calibración manual (ajusta según tu entorno)
black_value = 10   # valor típico sobre línea negra
white_value = 60   # valor típico sobre fondo claro
threshold = (black_value + white_value) / 2

def line_follower():
    global integral, last_error

    while True:
        # Lectura del sensor
        light_value = color_sensor.reflected_light_intensity

        # Error respecto al umbral
        error = threshold - light_value

        # PID
        integral += error
        derivative = error - last_error
        turn = Kp * error + Ki * integral + Kd * derivative

        # Ajustar velocidades
        left_speed = base_speed + turn
        right_speed = base_speed - turn

        # Limitar velocidades
        left_speed = max(min(left_speed, 50), -50)
        right_speed = max(min(right_speed, 50), -50)

        # Mover motores
        tank_drive.on(left_speed, right_speed)

        last_error = error
        time.sleep(0.01)

if __name__ == "__main__":
    try:
        line_follower()
    except KeyboardInterrupt:
        tank_drive.off()
        print("Programa detenido.")
