import socket
import threading
import time
import pyaudio
from vosk import Model, KaldiRecognizer
import json

# Tello IP and port
tello_address = ('192.168.10.1', 8889)
local_address = ('', 9000)

# UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(local_address)

# Load Vosk model
model = Model(r"C:\Users\Iraj Qureshi\drone\vosk-model-small-en-us-0.15")  # Change path if needed
recognizer = KaldiRecognizer(model, 16000)

# PyAudio init
mic = pyaudio.PyAudio()
listening = False
stop_program = False

# Send command to Tello
def send(message, delay=3):
    print(f"[SIMULATION] Would send to drone: {message}")
    time.sleep(delay)


# Listen for messages from Tello
def receive():
    global stop_program
    while True:
        try:
            response, _ = sock.recvfrom(128)
            print(f"📨 Tello says: {response.decode('utf-8')}")
        except Exception as e:
            print(f"❌ Error receiving: {e}")
            send("land", 5)
            sock.close()
            stop_program = True
            break

# Start listener thread
receive_thread = threading.Thread(target=receive)
receive_thread.daemon = True
receive_thread.start()

# Voice command recognizer
def get_command():
    global listening
    listening = True
    stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
    stream.start_stream()
    while listening:
        try:
            data = stream.read(4096, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                command = result.get("text", "").lower().strip()
                print(f"🎤 Recognized command: '{command}'")
                listening = False
                stream.stop_stream()
                stream.close()
                return command
        except Exception as e:
            print(f"❌ Microphone error: {e}")
            break

# Analyze voice and execute
def analyze_command(command):
    global stop_program
    try:
        if "take off" in command or "takeoff" in command:
            send("takeoff", 5)
        elif "land" in command:
            send("land", 5)
        elif "move up" in command or "go up" in command or "up" in command:
            send("up 100", 4)
        elif "front flip" in command or "flip front" in command:
            send("flip f", 4)
        elif "back flip" in command or "flip back" in command:
            send("flip b", 4)
        elif "say hi" in command or "spin" in command:
            send("cw 360", 4)
        elif "stop" in command:
            print("🛑 Stop command received. Landing and closing.")
            send("land", 4)
            sock.close()
            stop_program = True
        else:
            print(f"🤔 Unrecognized command: '{command}'")
    except Exception as e:
        print(f"❌ Error analyzing command: {e}")

# Main control loop
try:
    # Set Tello to command mode
    send("command", 3)
    send("battery?", 2)

    while not stop_program:
        print("🎙️ Waiting for voice command...")
        command = get_command()
        if command:
            analyze_command(command)
        else:
            print("⚠️ No command detected.")

finally:
    if not stop_program:
        print("🔒 Closing socket safely.")
        sock.close()
