import speech_recognition as sr

def check_mics():
    mics = sr.Microphone.list_microphone_names()
    print("\n--- AVAILABLE MICROPHONES ---")
    for index, name in enumerate(mics):
        print(f"Index {index}: {name}")
    
    print("\n-----------------------------")
    index = int(input("Enter the Index number of your main microphone: "))
    
    r = sr.Recognizer()
    with sr.Microphone(device_index=index) as source:
        print(f"\n[TEST] Speaking into Mic {index}...")
        print("[TEST] Adjusting for background noise (Please wait 1s)...")
        r.adjust_for_ambient_noise(source, duration=1)
        print("[TEST] Say something now!")
        try:
            audio = r.listen(source, timeout=5)
            print("[TEST] Audio captured! Converting to text...")
            text = r.recognize_google(audio)
            print(f"[SUCCESS] You said: '{text}'")
        except Exception as e:
            print(f"[FAILED] Error: {e}")

if __name__ == "__main__":
    check_mics()