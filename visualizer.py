import tkinter as tk
import math
import random
import ctypes  # <--- REQUIRED FOR TASKBAR ICON

class Particle:
    def __init__(self, canvas, cx, cy, radius, angle_h, angle_v):
        self.canvas = canvas
        self.cx = cx
        self.cy = cy
        self.dist = radius
        self.angle_h = angle_h
        self.angle_v = angle_v
        
        self.x = 0
        self.y = 0
        self.z = 0
        self.size = 2
        
        self.id = self.canvas.create_oval(0, 0, 0, 0, fill="#00FFFF", outline="")

    def update(self, rot_speed_x, rot_speed_y, color):
        self.angle_h += rot_speed_y
        self.angle_v += rot_speed_x
        self.x = self.dist * math.cos(self.angle_v) * math.sin(self.angle_h)
        self.y = self.dist * math.sin(self.angle_v)
        self.z = self.dist * math.cos(self.angle_v) * math.cos(self.angle_h)

        fov = 300 
        scale = fov / (fov + self.z)
        screen_x = self.cx + (self.x * scale)
        screen_y = self.cy + (self.y * scale)
        size = 2 * scale

        self.canvas.coords(self.id, screen_x-size, screen_y-size, screen_x+size, screen_y+size)
        self.canvas.itemconfig(self.id, fill=color)

class JarvisHUD:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Jarvis AI") # Shows in Taskbar
        
        # 1. Remove Borders
        self.root.overrideredirect(True)
        
        # 2. FORCE TASKBAR ICON
        self.force_taskbar_icon()

        self.root.attributes('-topmost', True)
        self.root.wm_attributes("-transparentcolor", "black")
        self.root.configure(bg='black')
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        size = 300 
        x_pos = (screen_width // 2) - (size // 2)
        y_pos = screen_height - 320
        self.root.geometry(f"{size}x{size}+{x_pos}+{y_pos}")

        self.canvas = tk.Canvas(self.root, width=size, height=size, bg="black", highlightthickness=0)
        self.canvas.pack()

        self.cx = size // 2
        self.cy = size // 2
        self.particles = []
        num_particles = 250
        sphere_radius = 70 
        phi = math.pi * (3. - math.sqrt(5.))
        
        for i in range(num_particles):
            y = 1 - (i / float(num_particles - 1)) * 2
            radius = math.sqrt(1 - y * y)
            theta = phi * i
            angle_h = theta
            angle_v = math.asin(y)
            p = Particle(self.canvas, self.cx, self.cy, sphere_radius, angle_h, angle_v)
            self.particles.append(p)

        self.state = "IDLE"
        
        # --- RECORDING INDICATOR (NEW) ---
        # A Red Dot and "REC" text hidden by default
        self.rec_indicator = self.canvas.create_oval(250, 20, 270, 40, fill="red", outline="white", state='hidden')
        self.rec_text = self.canvas.create_text(230, 30, text="REC", fill="red", font=("Arial", 10, "bold"), state='hidden')
        
        self.is_recording = False
        self.blink_state = False
        
        # 3. Enable Right-Click to Quit
        self.create_context_menu()
        
        self.animate()

    def force_taskbar_icon(self):
        # Magic Windows code to show icon for borderless window
        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        style = style & ~0x00000080
        style = style | 0x00040000
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
        self.root.withdraw()
        self.root.after(10, self.root.deiconify)

    def create_context_menu(self):
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Quit Jarvis", command=self.close_app)
        self.root.bind("<Button-3>", self.show_menu)

    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def close_app(self):
        self.root.destroy()
        import sys
        sys.exit()

    # --- THREAD-SAFE UPDATE METHODS (FIXES FREEZING) ---

    def set_state(self, new_state, text=None):
        """Safely updates the state from the background thread."""
        self.state = new_state
        # self.state is read by the animation loop, so direct assignment is fine here.

    def set_recording(self, status):
        """Safely schedules the GUI update on the main thread."""
        self.root.after(0, lambda: self._update_recording_ui(status))

    def _update_recording_ui(self, status):
        """The actual UI update (Must run on Main Thread)."""
        self.is_recording = status
        state = 'normal' if status else 'hidden'
        
        try:
            self.canvas.itemconfig(self.rec_indicator, state=state)
            self.canvas.itemconfig(self.rec_text, state=state)
        except:
            pass

    def animate(self):
        self.root.lift()
        self.root.attributes('-topmost', True)
        rot_speed_x = 0.01
        rot_speed_y = 0.02
        color = "#00FFFF" 

        if self.state == "IDLE":
            rot_speed_x = 0.005
            rot_speed_y = 0.02
            color = "#0088FF"
        elif self.state == "LISTENING":
            rot_speed_x = 0.01
            rot_speed_y = 0.01
            color = "#00FF00"
        elif self.state == "PROCESSING":
            rot_speed_x = 0.05
            rot_speed_y = 0.05
            color = "#FF00FF"
        elif self.state == "SPEAKING":
            rot_speed_x = 0.02
            rot_speed_y = 0.02
            if random.random() > 0.5: color = "#FFFFFF"
            else: color = "#00FFFF"

        # --- BLINK LOGIC FOR RECORDING ---
        if self.is_recording:
            # Randomly toggle blink for "recording" effect
            if random.random() < 0.05: 
                self.blink_state = not self.blink_state
                state = 'normal' if self.blink_state else 'hidden'
                self.canvas.itemconfig(self.rec_indicator, state=state)

        for p in self.particles:
            p.update(rot_speed_x, rot_speed_y, color)

        self.root.after(20, self.animate)

    def start(self):
        self.root.mainloop()