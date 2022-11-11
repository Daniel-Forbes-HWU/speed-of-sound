from pico_speed_of_sound import run_speed_of_sound
SPEAKER_PIN:int = 0  # GPIO Pin connected to speaker
MICROPHONE_PIN:int = 1  # GPIO Pin connected to microphone
SAMPLE_DELAY_MS:int = 50  # Minimum time between measurements
STATUS_LED_PIN:int = 22  # Pin for the power led
run_speed_of_sound(SPEAKER_PIN, MICROPHONE_PIN, STATUS_LED_PIN, SAMPLE_DELAY_MS)
