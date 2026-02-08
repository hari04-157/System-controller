import ollama
import json
import re

# --- FAST TRACK: SKIPS AI FOR SPEED ---
def fast_track_command(text):
    text = text.lower().strip()
    
    if "volume" in text:
        if "up" in text or "increase" in text:
            return {"tool": "volume", "args": "up"}
        if "down" in text or "decrease" in text:
            return {"tool": "volume", "args": "down"}
        if "set" in text:
            # Extracts numbers like "75" from "set volume to 75"
            nums = re.findall(r'\d+', text)
            if nums:
                return {"tool": "volume", "args": f"set|{nums[0]}"}

    # --- NEW: NIGHT MODE ---
    if "night mode" in text or "dark mode" in text:
        if "on" in text or "enable" in text:
            return {"tool": "night_mode", "args": "on"}
        if "off" in text or "disable" in text:
            return {"tool": "night_mode", "args": "off"}
    
# ... inside fast_track_command ...

    # --- NIGHT LIGHT ---
    if "night light" in text or "blue light" in text:
        # Since we are just toggling the button, we don't strictly need "on/off" logic 
        # for the simpler version, but we can pass it anyway.
        return {"tool": "night_light", "args": "toggle"}
    
    # ... inside fast_track_command ...

    # --- NEW: BRIGHTNESS ---
    if "brightness" in text:
        if "up" in text or "increase" in text or "high" in text:
            return {"tool": "brightness", "args": "up"}
        if "down" in text or "decrease" in text or "low" in text or "dim" in text:
            return {"tool": "brightness", "args": "down"}
        if "set" in text:
            nums = re.findall(r'\d+', text)
            if nums:
                return {"tool": "brightness", "args": f"set|{nums[0]}"}

    # 1. Open App / Website
    if text.startswith("open ") or text.startswith("launch "):
        target = text.replace("open ", "").replace("launch ", "").strip()
        if "." in target or "folder" in text: 
            return None 
        return {"tool": "open_app", "args": target}

    # 2. Close App
    if text.startswith("close "):
        target = text.replace("close ", "").strip()
        return {"tool": "close_app", "args": target}

    # 3. System Ops
    if "shutdown" in text: return {"tool": "system_ops", "args": "shutdown"}
    if "restart" in text: return {"tool": "system_ops", "args": "restart"}
    if "sleep" in text and "mode" in text: return {"tool": "system_ops", "args": "sleep"}
    if "lock pc" in text or "lock computer" in text: return {"tool": "system_ops", "args": "lock"}

    # 4. Search
    if text.startswith("search for ") or text.startswith("google "):
        query = text.replace("search for ", "").replace("google ", "").strip()
        return {"tool": "search", "args": query}

    # 5. WhatsApp Calls (NEW FAST TRACK)
    # This prevents the AI from getting confused and printing code.
    if text.startswith("call ") or text.startswith("video call ") or "make a video call" in text:
        # Determine Name
        name = text.replace("make a ", "").replace("video call ", "").replace("call ", "").replace("to ", "").strip()
        
        # Determine Type
        call_type = "video" if "video" in text else "audio"
        
        return {"tool": "whatsapp_call", "args": f"{name}|{call_type}"}

    return None

def get_command(user_text):
    # STEP 1: Try Fast Track (0.01s)
    fast_decision = fast_track_command(user_text)
    if fast_decision:
        return fast_decision

    # STEP 2: Fallback to AI (2-5s)
    system_prompt = """
    You are a Windows Automation Agent. Map the user's request to the correct JSON tool.
    
    === TOOLS ===
    1. "file_ops": Opening Folders & Files.
       - "Open folder Photos" -> {"tool": "file_ops", "args": "open|Photos"}
       - "Open file notes.txt" -> {"tool": "file_ops", "args": "open|notes.txt"}
       - "Delete test.txt" -> {"tool": "file_ops", "args": "delete|test.txt"}

    2. "hotkey": GUI Selection & Actions (The User's Keyboard).
       - "Select all" -> {"tool": "hotkey", "args": "ctrl+a"}
       - "Select all and delete" -> {"tool": "hotkey", "args": "ctrl+a, delete"}
       - "Copy this" -> {"tool": "hotkey", "args": "ctrl+c"}
       - "Paste here" -> {"tool": "hotkey", "args": "ctrl+v"}
       - "Enter folder" -> {"tool": "hotkey", "args": "enter"}

    3. "system_ops": Power commands.
       - "Shutdown" -> {"tool": "system_ops", "args": "shutdown"}
       - "Restart" -> {"tool": "system_ops", "args": "restart"}
       - "Sleep" -> {"tool": "system_ops", "args": "sleep"}
       - "Lock pc" -> {"tool": "system_ops", "args": "lock"}

    4. "open_app": Use this to OPEN applications.
       - "Open WhatsApp" -> {"tool": "open_app", "args": "whatsapp"}

    5. "close_app": Use this to CLOSE applications.
       - "Close WhatsApp" -> {"tool": "close_app", "args": "whatsapp"}
       - "Close all apps" -> {"tool": "close_app", "args": "all"}

    6. "whatsapp": Use this ONLY for SENDING MESSAGES.
       - "Message Dad 'Hello'" -> {"tool": "whatsapp", "args": "Dad|Hello"}

    7. "search": Web Search.
       - "Search for cats" -> {"tool": "search", "args": "cats"}

    8. "whatsapp": Send messages. EXTRACT THE NAME AND THE EXACT MESSAGE.
       - "Tell Dad that I am busy today" -> {"tool": "whatsapp", "args": "Dad|I am busy today"}
       - "Send a message to Mom saying I will be late" -> {"tool": "whatsapp", "args": "Mom|I will be late"}
       - "Message John hello" -> {"tool": "whatsapp", "args": "John|hello"}

    9. "youtube": Play specific videos or movies on YouTube.
       - "Play Iron Man trailer" -> {"tool": "youtube", "args": "Iron Man trailer"}
       - "Play relaxing rain sounds" -> {"tool": "youtube", "args": "relaxing rain sounds"}
    
    10. "whatsapp_call": Make audio or video calls.
       - "Call Harish" -> {"tool": "whatsapp_call", "args": "Harish|audio"}
       - "Video call Dad" -> {"tool": "whatsapp_call", "args": "Dad|video"}
    
    11. "volume": Control audio levels.
        - "Volume up" -> {"tool": "volume", "args": "up"}
        - "Decrease volume" -> {"tool": "volume", "args": "down"}
        - "Set volume to 50" -> {"tool": "volume", "args": "set|50"}
    
    12. "night_mode": Toggle system theme.
        - "Night mode on" -> {"tool": "night_mode", "args": "on"}
        - "Dark mode off" -> {"tool": "night_mode", "args": "off"}

    OUTPUT FORMAT:
    Return ONLY valid JSON. Example: {"tool": "close_app", "args": "whatsapp"}
    """

    try:
        response = ollama.chat(model='llama3', messages=[ 
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_text},
        ])
        
        content = response['message']['content']
        
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end != 0:
            json_str = content[start:end]
            return json.loads(json_str)
        
        return None

    except Exception as e:
        print(f"[Brain Error] {e}")
        return None