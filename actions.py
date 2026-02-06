import os
import subprocess
import pyautogui
import time
import psutil 
import pyttsx3 
import webbrowser 
from send2trash import send2trash
# REMOVED: from AppOpener import open as app_open... (This fixes the crash)
import pywhatkit

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