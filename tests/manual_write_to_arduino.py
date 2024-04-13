
import time
import serial

dt = 0.5
with serial.Serial(
    port="COM3", baudrate=19200, timeout=0.1
) as arduino:

    for i in range(20):
        print(f"Loop {i}")

        arduino.write("u\n".encode())
        time.sleep(dt)
        print(arduino.read(100))

        arduino.write("d\n".encode())
        time.sleep(dt)
        print(arduino.read(100))


