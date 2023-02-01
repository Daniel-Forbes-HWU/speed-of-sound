def run_speed_of_sound(speaker_pin:int, microphone_pin:int, led_pin:int, sample_delay_ms:int=50):
    from machine import Pin, PWM
    from utime import sleep_ms, ticks_cpu, ticks_diff 
    
    # Params
    LED_BRIGHTNESS = 0.05  # LED Duty cycle

    # Initialise speaker and microphone pins
    speaker = Pin(speaker_pin, Pin.OUT, Pin.PULL_DOWN)
    microphone = Pin(microphone_pin, Pin.IN, Pin.PULL_UP)
    led = PWM(Pin(led_pin, Pin.OUT, Pin.PULL_UP))

    # Turn on status led - PWM
    led.duty_u16(int(65535*LED_BRIGHTNESS))

    def wait_for_falling(pin:Pin) -> int:
        # TODO add timeout
        while pin.value():  # Wait until pin goes low
            pass
        return ticks_cpu()  # Once pin has gone low

    def measure(repetitions:int):
        # Perform measurements
        while repetitions > 0:
            
            # Send acoustic pulse
            speaker.high()  
            start_time = ticks_cpu()  # Get current time
            
            # Wait for microphone to detect acoustic pressure wave
            end_time = wait_for_falling(microphone)  
            
            speaker.low()
            
            # Calculate travel time
            acoustic_wave_travel_time = ticks_diff(end_time, start_time) 
            
            # Send travel time over usb serial
            print(acoustic_wave_travel_time)
            
            sleep_ms(sample_delay_ms)

            repetitions -= 1

    # Endless loop
    while True:
        try:
            repetitions = int(input())  # Read number of repetitions from serial
        except:  # If it reads something that isn't a number, ignore it
            continue
        measure(repetitions)  # Perform measurement 