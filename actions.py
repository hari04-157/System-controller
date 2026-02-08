import os
import subprocess
import pyautogui
import time
import psutil 
import pyttsx3 
import webbrowser 
from send2trash import send2trash
import screen_brightness_control as sbc
# REMOVED: from AppOpener import open as app_open... (This fixes the crash)
import pywhatkit
# ... existing imports ...
import winreg  # Built-in, for Night Mode
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# --- FIXED VOICE FUNCTION ---
def speak(text):
    """Speaks text aloud. Initializes engine every time to prevent freezing."""
    print(f"[Jarvis] {text}") 
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)
        voices = engine.getProperty('voices')
        if len(voices) > 1:
            engine.setProperty('voice', voices[0].id)
        else:
            engine.setProperty('voice', voices[1].id)

        engine.say(text)
        engine.runAndWait() 
    except Exception as e:
        print(f"[Voice Error] Could not speak: {e}")

# --- HELPER FUNCTIONS ---
def get_safe_pids():
    safe_pids = [os.getpid()]
    try:
        parent = psutil.Process(os.getpid()).parent()
        if parent: safe_pids.append(parent.pid)
    except: pass
    return safe_pids

def is_match(name1, name2):
    n1 = name1.lower().replace(" ", "").replace("-", "").replace("_", "")
    n2 = name2.lower().replace(" ", "").replace("-", "").replace("_", "")
    return n1 == n2 or n2 in n1 

# --- ROBUST APP CLOSER ---
def find_and_kill_process(user_app_name):
    user_app_name = user_app_name.lower().strip()
    aliases = {
        "edge": "msedge", "microsoft edge": "msedge",
        "chrome": "chrome", "google chrome": "chrome",
        "calculator": "calc", "notepad": "notepad",
        "spotify": "spotify", "discord": "discord",
        "vlc": "vlc", "word": "winword",
        "excel": "excel", "powerpoint": "powerpnt",
        "crunchyroll": "crunchyroll"
    }
    
    target_process = aliases.get(user_app_name, user_app_name)
    killed_count = 0

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['pid'] < 100: continue 
            p_name = proc.info['name'].lower().replace(".exe", "")
            
            if p_name == target_process:
                proc.kill()
                killed_count += 1
                continue

            if len(user_app_name) > 3 and user_app_name in p_name:
                proc.kill()
                killed_count += 1
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    return killed_count > 0

def find_folder_recursive(folder_name):
    user_path = os.path.expanduser("~")
    root_drive = "C:\\"
    print(f"[System] Searching for '{folder_name}'...")

    priority_locs = ["Desktop", "Downloads", "Documents", "Pictures", "Music", "Videos"]
    
    try:
        if os.path.isdir(os.path.join(root_drive, folder_name)):
            return os.path.join(root_drive, folder_name)
        for item in os.listdir(root_drive):
             if is_match(item, folder_name) and os.path.isdir(os.path.join(root_drive, item)):
                 return os.path.join(root_drive, item)
    except: pass

    for loc in priority_locs:
        full_path = os.path.join(user_path, loc)
        try:
            if os.path.isdir(os.path.join(full_path, folder_name)):
                 return os.path.join(full_path, folder_name)
            for item in os.listdir(full_path):
                if is_match(item, folder_name) and os.path.isdir(os.path.join(full_path, item)):
                    return os.path.join(full_path, item)
        except: pass

    print(f"[System] Quick search failed. Starting Deep Scan...")
    exclude_dirs = {"Windows", "ProgramData", "$Recycle.Bin", "System Volume Information", "Program Files", "Program Files (x86)"}
    
    for root, dirs, files in os.walk(root_drive):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for d in dirs:
            if is_match(d, folder_name):
                return os.path.join(root, d)
    return None

def play_youtube(query):
    speak(f"Playing {query} on YouTube.")
    pywhatkit.playonyt(query)

# --- NEW FEATURES: VOLUME & NIGHT MODE ---

# --- ROBUST VOLUME CONTROL (Keyboard Method) ---
# This bypasses the crashing pycaw library and uses media keys directly.

def volume_control(command):
    try:
        # 1. VOLUME UP
        if "up" in command or "increase" in command:
            speak("Increasing volume.")
            # Pressing it 5 times gives a noticeable boost (10%)
            for _ in range(5):
                pyautogui.press("volumeup")

        # 2. VOLUME DOWN
        elif "down" in command or "decrease" in command:
            speak("Decreasing volume.")
            for _ in range(5):
                pyautogui.press("volumedown")

        # 3. SET SPECIFIC VOLUME (e.g. "Set volume to 50")
        elif "set" in command:
            try:
                # Extract the number (e.g. 50)
                val = int(command.split("|")[1])
                speak(f"Setting volume to {val} percent.")
                
                # Hack: Reset to 0 first, then go up.
                # Windows usually has 50 steps (2% per step).
                # So to get to 0, we press down 50 times.
                for _ in range(50):
                    pyautogui.press("volumedown")
                
                # Now go up to the target level
                # target / 2 gives the number of key presses needed
                steps = int(val / 2)
                for _ in range(steps):
                    pyautogui.press("volumeup")
                    
            except Exception as e:
                print(f"Volume Set Error: {e}")
                speak("I couldn't set that specific level.")
                
    except Exception as e:
        print(f"Volume Action Error: {e}")
        speak("I encountered a problem adjusting the volume.")

# (You can remove the old 'get_volume_control' function entirely, it is no longer needed)
# --- COMMAND ACTIONS ---

def system_control(command):
    if command == "shutdown":
        speak("Shutting down the system.")
        os.system("shutdown /s /t 0")
    elif command == "restart":
        speak("Restarting the system.")
        os.system("shutdown /r /t 0")
    elif command == "sleep":
        speak("Entering sleep mode.")
        cmd = "powershell -command \"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false)\""
        os.system(cmd)
    elif command == "lock":
        speak("Locking workstation.")
        os.system("rundll32.exe user32.dll,LockWorkStation")

def open_app(app_name):
    speak(f"Opening {app_name}")
    try:
        # --- FIX: IMPORT HERE TO PREVENT CRASH ---
        from AppOpener import open as app_open
        app_open(app_name, match_closest=True, output=False)
    except:
        try:
            print(f"[System] Standard open failed. Trying Windows Search for {app_name}...")
            pyautogui.hotkey('win')
            time.sleep(0.5)
            pyautogui.write(app_name)
            time.sleep(1.0) 
            pyautogui.press('enter')
        except Exception as e:
            print(f"Could not open app: {e}")

def close_app_logic(app_name):
    speak(f"Closing {app_name}")
    safe_pids = get_safe_pids()
    target_apps = ["whatsapp", "telegram", "chrome", "msedge", "notepad", "calculator", "spotify", "vlc", "discord", "explorer"]

    if app_name.lower() in ["all", "everything"]:
        speak("Closing all non-essential applications.")
        count = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['pid'] in safe_pids: continue
                if "code" in proc.info['name'].lower() or "python" in proc.info['name'].lower(): continue
                
                proc_name_clean = proc.info['name'].lower().replace(".exe", "")
                if any(target in proc_name_clean for target in target_apps):
                    proc.kill()
                    count += 1
            except: pass
        speak(f"Closed {count} apps.")
    else:
        success = find_and_kill_process(app_name)
        
        if not success:
            try:
                # --- FIX: IMPORT HERE TO PREVENT CRASH ---
                from AppOpener import close as app_close
                app_close(app_name, match_closest=True, output=False)
                os.system(f"taskkill /f /im {app_name}.exe >nul 2>&1")
            except: pass

def run_shell(command):
    speak("Executing shell command.")
    try: subprocess.run(command, shell=True)
    except: pass

def file_manager(instruction):
    if not instruction: return
    
    cmd = instruction.lower().strip()
    if cmd in ["explorer", "open", "file explorer", "open file explorer", "my computer", "this pc"]:
        speak("Opening File Explorer.")
        os.startfile(os.path.expanduser("~"))
        return

    try:
        if "|" not in instruction:
            action = "open"
            target = instruction
        else:
            parts = instruction.split("|", 1)
            action, target = parts
            target = target.strip()

        found_path = None
        paths = [
            os.path.join(os.path.expanduser("~"), "Desktop", target),
            os.path.join(os.path.expanduser("~"), "Downloads", target)
        ]
        found_path = next((p for p in paths if os.path.exists(p)), None)
        
        if not found_path and action == "open":
            found_path = find_folder_recursive(target)

        if not found_path:
            speak(f"I could not find {target}.")
            return

        if action == "delete":
            speak(f"Deleting {target}.")
            send2trash(found_path)
        elif action == "open":
            speak(f"Opening {target}.")
            os.startfile(found_path)
            
    except Exception as e:
        print(f"File Error: {e}")

def send_whatsapp(args):
    if not args or "|" not in args: open_app("whatsapp"); return
    try:
        name, msg = args.split("|", 1)
        name = name.strip()
        msg = msg.strip()
        
        speak(f"Messaging {name}.")
        
        # Open using local import if needed, or rely on open_app function
        open_app("whatsapp")
        time.sleep(1.5) 
        
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.3)
        pyautogui.write(name)
        time.sleep(0.8) 
        
        pyautogui.press('down')
        pyautogui.press('enter')
        time.sleep(0.5)
        
        pyautogui.write(msg, interval=0.005) 
        time.sleep(0.5)
        pyautogui.press('enter')
        
        speak("Message sent.")
    except Exception as e: print(f"WhatsApp Error: {e}")

def press_keys(keys):
    if not keys: return
    speak(f"Pressing keys: {keys}")
    commands = keys.split(",") 
    for cmd in commands:
        cmd = cmd.strip()
        if "+" in cmd: pyautogui.hotkey(*cmd.split("+"))
        else: pyautogui.press(cmd)
        time.sleep(0.1)

def make_whatsapp_call(args):
    if not args or "|" not in args: 
        speak("I need a name and call type.")
        return
        
    try:
        name, call_type = args.split("|", 1)
        name = name.strip()
        call_type = call_type.strip().lower()
        
        speak(f"Starting {call_type} call to {name}.")
        
        os.system('echo. | clip') 
        open_app("whatsapp")
        time.sleep(2.0) 
        
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.5)
        pyautogui.write(name)
        time.sleep(1.5) 
        
        pyautogui.press('down')
        pyautogui.press('enter')
        time.sleep(3.0) 
        
        if "video" in call_type:
            pyautogui.hotkey('ctrl', 'shift', 'v')
        else:
            pyautogui.hotkey('ctrl', 'shift', 'c')
            
        time.sleep(1.0) 
        
        # --- YOUR COORDINATES GO HERE ---
        # Don't forget to update these with numbers from get_coords.py!
        YOUR_VIDEO_X = 163  
        YOUR_VIDEO_Y = 225  
        
        YOUR_AUDIO_X = YOUR_VIDEO_X - 60 
        YOUR_AUDIO_Y = YOUR_VIDEO_Y

        if "video" in call_type:
            pyautogui.click(x=YOUR_VIDEO_X, y=YOUR_VIDEO_Y)
        else:
            pyautogui.click(x=YOUR_AUDIO_X, y=YOUR_AUDIO_Y)
                
    except Exception as e:
        print(f"WhatsApp Call Error: {e}")
        speak("I encountered an error trying to place the call.")

# --- NIGHT MODE CONTROL ---
def night_mode_control(state):
    """Toggles Windows Dark Mode (Apps & System)."""
    speak(f"Turning Dark Mode {state}...")
    try:
        # 1. Define the Registry Path
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        
        # 2. Determine Value (0 = Dark, 1 = Light)
        # If user says "on", we want Dark Mode (Value 0)
        # If user says "off", we want Light Mode (Value 1)
        value = 0 if state == "on" else 1 
        
        # 3. Open Registry Key
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        except:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        
        # 4. Set both Apps and System theme
        winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, value)
        winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, value)
        
        winreg.CloseKey(key)
        
        speak(f"Dark mode is now {state}.")
        
    except Exception as e:
        print(f"Night Mode Error: {e}")
        speak("I could not change the theme.")

# --- REAL WINDOWS NIGHT LIGHT (via Settings) ---
def night_light_control(state):
    """
    Opens Windows Settings to toggle the real Night Light feature.
    """
    speak("Toggling Windows Night Light.")
    
    # 1. Open the specific Settings Page
    os.system("start ms-settings:nightlight")
    
    # 2. Wait for the window to load (Adjust time if your PC is slow)
    time.sleep(2.0) 
    
    # 3. Press 'Space' to toggle the button
    # (The "Turn on now" button is usually selected by default)
    pyautogui.press('space') 
    
    # 4. Close the window
    time.sleep(0.5)
    pyautogui.hotkey('alt', 'f4')

# --- BRIGHTNESS CONTROL ---
def brightness_control(command):
    try:
        # Get current brightness (returns a list, we take the first screen)
        current = sbc.get_brightness()
        if not current:
            speak("I cannot detect a screen to adjust.")
            return
            
        current_level = current[0]
        
        # 1. SET SPECIFIC VALUE (e.g. "Set brightness to 50")
        if "set" in command:
            try:
                val = int(command.split("|")[1])
                # Ensure value is between 0 and 100
                new_level = max(0, min(100, val)) 
                sbc.set_brightness(new_level)
                speak(f"Brightness set to {new_level} percent.")
            except:
                speak("I couldn't understand the brightness level.")
        
        # 2. INCREASE
        elif "up" in command or "increase" in command:
            if current_level >= 100:
                speak("Brightness is already at maximum.")
            else:
                new_level = min(100, current_level + 10)
                sbc.set_brightness(new_level)
                speak("Brightness increased.")

        # 3. DECREASE
        elif "down" in command or "decrease" in command or "dim" in command:
            if current_level <= 0:
                speak("Brightness is already at minimum.")
            else:
                new_level = max(0, current_level - 10)
                sbc.set_brightness(new_level)
                speak("Brightness decreased.")
                
    except Exception as e:
        print(f"Brightness Error: {e}")
        speak("I encountered a problem adjusting the brightness.")