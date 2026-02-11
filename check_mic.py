import speech_recognition as sr

# These are the three indexes for your Intel Smart Sound Mic
test_indexes = [2, 7, 12]

print("--- STARTING HARDWARE TEST ---")

for idx in test_indexes:
    print(f"\n--- Testing Index {idx} ---")
    r = sr.Recognizer()
    try:
        with sr.Microphone(device_index=idx) as source:
            print("Calibrating... please wait 1 second.")
            r.adjust_for_ambient_noise(source, duration=1)
            
            print(f">>> SPEAK NOW INTO THE LAPTOP (Testing {idx}) <<<")
            # We use a short timeout so you don't wait forever if it's dead
            audio = r.listen(source, timeout=4, phrase_time_limit=3)
            
            print(f"✅ SUCCESS! Index {idx} successfully captured audio.")
    
    except sr.WaitTimeoutError:
        print(f"❌ FAILED! Index {idx} heard nothing (Timed out).")
    except Exception as e:
        print(f"❌ ERROR on Index {idx}: {e}")

print("\n--- TEST COMPLETE ---")