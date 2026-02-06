import pyautogui
import time

print("--- MOUSE TRACKER ---")
print("1. Open WhatsApp and open a chat.")
print("2. Move your mouse HOVERING OVER the 'Video Call' icon.")
print("3. Wait 5 seconds...")

time.sleep(5)

x, y = pyautogui.position()
print(f"\n✅ YOUR EXACT COORDINATES: x={x}, y={y}")
print("---------------------")
print(f"Write these numbers down!")