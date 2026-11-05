#Pico heartbeat watchdog prototype (using Wokwi MicroPython simulator)

from machine import Pin
import time

# GPIO connections
heartbeat = Pin(16, Pin.IN, Pin.PULL_DOWN)
fan_enable = Pin(15, Pin.OUT, value=0)
fault_led = Pin(17, Pin.OUT, value=1)

# Shut off the fan after 3 seconds without a heartbeat.
TIMEOUT_MS = 3000


class Watchdog:
    def __init__(self):
        self.previous = 0
        self.last_pulse = None

    def update(self, level, now):
        # A rising edge is a change from LOW to HIGH.
        if level == 1 and self.previous == 0:
            self.last_pulse = now

        self.previous = level

        # Healthy only after a pulse has arrived and
        # fewer than 3 seconds have passed since it.
        return (
            self.last_pulse is not None
            and time.ticks_diff(now, self.last_pulse) < TIMEOUT_MS
        )


def run():
    watchdog = Watchdog()
    last_state = None

    print("Pico watchdog started")
    print("Heartbeat: GP16 | Fan enable: GP15 | Fault LED: GP17")
    print("Heartbeat timeout: 3 seconds")

    while True:
        healthy = watchdog.update(
            heartbeat.value(),
            time.ticks_ms()
        )

        fan_enable.value(1 if healthy else 0)
        fault_led.value(0 if healthy else 1)

        # Print only when the system changes state.
        if healthy != last_state:
            if healthy:
                print("HEALTHY: heartbeat detected; fan-enable ON")
            else:
                print("FAULT / WAITING: fan-enable OFF")

            last_state = healthy

        time.sleep_ms(10)


if __name__ == "__main__":
    run()
