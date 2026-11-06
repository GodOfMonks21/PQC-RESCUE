import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

HEARTBEAT_PIN = 22
HEARTBEAT_PERIOD = 0.5


def run():
    if GPIO is None:
        print("Simulation mode")
    else:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(HEARTBEAT_PIN, GPIO.OUT, initial=GPIO.LOW)

    print("Pi heartbeat sender started")

    try:
        while True:
            if GPIO is not None:
                GPIO.output(HEARTBEAT_PIN, GPIO.HIGH)

            print("Heartbeat HIGH")
            time.sleep(HEARTBEAT_PERIOD / 2)

            if GPIO is not None:
                GPIO.output(HEARTBEAT_PIN, GPIO.LOW)

            print("Heartbeat LOW")
            time.sleep(HEARTBEAT_PERIOD / 2)

    except KeyboardInterrupt:
        print("Heartbeat sender stopped")

    finally:
        if GPIO is not None:
            GPIO.output(HEARTBEAT_PIN, GPIO.LOW)
            GPIO.cleanup()


if __name__ == "__main__":
    run()
