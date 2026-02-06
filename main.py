import speech_recognition as sr
import brain
import actions
import sys
import time
import threading
import socket      # <--- NEW IMPORT
import subprocess  # <--- NEW IMPORT
from visualizer import JarvisHUD 

hud = None

# --- NEW FUNCTION: AUTO-START OLLAMA ---
def ensure_ollama_server():
    """Checks if Ollama is running. If not, starts it silently."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 11434))
    sock.close()
    
    if result != 0:
        print("[System] Neural Engine (Ollama) is offline.")
        print("[System] Starting Neural Engine...")
        try:
            # Starts Ollama in the background (hidden window)
            # creationflags=0x08000000 is CREATE_NO_WINDOW on Windows
            subprocess.Popen(["ollama", "serve"], creationflags=0x08000000)
            time.sleep(5) # Give it 5 seconds to load the model into RAM
            print("[System] Neural Engine started successfully.")
        except FileNotFoundError:
            print("[ERROR] Could not find 'ollama'. Is it installed and in your PATH?")
    else:
        print("[System] Neural Engine attached.")

def run_jarvis_logic():
    r = sr.Recognizer()
    r.pause_threshold = 0.6 
    r.dynamic_energy_threshold = True 
    r.energy_threshold = 400 

    if hud: hud.set_state("PROCESSING", "Calibrating...")
    print("\n[System] Calibrating microphone...")
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1.0)
    
    actions.speak("System Online.")
    
    while True:
        try:
            if hud: hud.set_state("LISTENING", "Listening...")
            
            command_text = ""
            with sr.Microphone(device_index=2) as source:
                try:
                    audio = r.listen(source, timeout=5, phrase_time_limit=10) 
                    
                    if hud: hud.set_state("PROCESSING", "Processing...")
                    print("Processing...", end="\r")
                    command_text = r.recognize_google(audio)
                    print(f"\nYou said: {command_text}")
                except sr.WaitTimeoutError: pass
                except sr.UnknownValueError: pass
                except Exception: pass

            if command_text:
                cmd_lower = command_text.lower()
                
                if "exit" in cmd_lower or "stop" in cmd_lower:
                    if hud: hud.set_state("SPEAKING", "Goodbye")
                    actions.speak("Disconnecting.")
                    sys.exit()

                decision = brain.get_command(cmd_lower)
                
                if decision:
                    tool = decision.get('tool')
                    args = decision.get('args')
                    print(f"[AI Decision] Tool: {tool} | Args: {args}")
                    
                    if hud: hud.set_state("SPEAKING", f"{tool}")
                    
                    if tool == "system_ops": actions.system_control(args)
                    elif tool == "open_app": actions.open_app(args)
                    elif tool == "close_app": actions.close_app_logic(args)
                    elif tool == "shell": actions.run_shell(args)
                    elif tool == "file_ops": actions.file_manager(args)
                    elif tool == "hotkey": actions.press_keys(args)
                    elif tool == "whatsapp": actions.send_whatsapp(args)
                    elif tool == "whatsapp_call": actions.make_whatsapp_call(args)
                    elif tool == "youtube": actions.play_youtube(args) 
                    elif tool == "search":
                        actions.speak(f"Searching for {args}")
                        import webbrowser
                        webbrowser.open(f"https://www.google.com/search?q={args}")
                else:
                    if hud: hud.set_state("IDLE", "Unsure")
                    print("I didn't understand that command.")
            else:
                if hud: hud.set_state("IDLE", "Standing By")
            
            time.sleep(0.1)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    global hud
    ensure_ollama_server() # <--- CHECKS SERVER BEFORE GUI STARTS
    print("--- DYNAMIC JARVIS ONLINE ---")
    hud = JarvisHUD()
    t = threading.Thread(target=run_jarvis_logic)
    t.daemon = True
    t.start()
    hud.start()

if __name__ == "__main__":
    main()