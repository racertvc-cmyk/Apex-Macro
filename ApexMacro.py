import os
import sys
import json
import time
import shutil
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

# Global variables for dynamic import
mouse = None
keyboard = None

def try_import_pynput():
    global mouse, keyboard
    try:
        from pynput import mouse as m, keyboard as k
        mouse = m
        keyboard = k
        return True
    except ImportError:
        return False

class DependencyLoader:
    """A beautiful dark-themed splash screen to handle automatic installation of pynput."""
    def __init__(self, on_success_callback):
        self.on_success = on_success_callback
        self.root = tk.Tk()
        self.root.title("Apex Loader")
        self.root.geometry("380x180")
        self.root.configure(bg="#121212")
        
        # Center splash window
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = (ws / 2) - (380 / 2)
        y = (hs / 2) - (180 / 2)
        self.root.geometry(f"+{int(x)}+{int(y)}")
        
        # Apply dark title bar if on Windows
        self.apply_dark_title_bar()

        # UI elements
        self.label_title = tk.Label(
            self.root, 
            text="APEX MACRO", 
            fg="#a855f7", 
            bg="#121212", 
            font=("Segoe UI", 16, "bold")
        )
        self.label_title.pack(pady=(20, 5))

        self.label_status = tk.Label(
            self.root, 
            text="Checking system dependencies...", 
            fg="#9ca3af", 
            bg="#121212", 
            font=("Segoe UI", 9)
        )
        self.label_status.pack(pady=5)

        # Custom progress bar line
        self.progress_canvas = tk.Canvas(self.root, width=280, height=4, bg="#1a1a1a", highlightthickness=0)
        self.progress_canvas.pack(pady=10)
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 4, fill="#a855f7", outline="")

        self.ok_button = None
        self.root.after(100, self.check_and_load)
        self.root.mainloop()

    def apply_dark_title_bar(self):
        self.root.update()
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                if hwnd == 0:
                    hwnd = self.root.winfo_id()
                rendering_policy = ctypes.c_int(1)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(rendering_policy), ctypes.sizeof(rendering_policy))
            except Exception:
                pass

    def animate_progress(self, target_w, current_w=0):
        if current_w < target_w:
            current_w += 10
            self.progress_canvas.coords(self.progress_bar, 0, 0, current_w, 4)
            self.root.after(15, lambda: self.animate_progress(target_w, current_w))

    def check_and_load(self):
        if try_import_pynput():
            self.animate_progress(280)
            self.label_status.configure(text="All required packages found!", fg="#34d399")
            self.show_success_state()
        else:
            self.label_status.configure(text="pynput is missing. Installing automatically...", fg="#f59e0b")
            threading.Thread(target=self.install_dependencies_thread, daemon=True).start()

    def install_dependencies_thread(self):
        try:
            self.root.after(10, lambda: self.animate_progress(100))
            
            # Install package via pip
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pynput"])
            
            # Recheck
            if try_import_pynput():
                self.root.after(0, lambda: self.animate_progress(280))
                self.root.after(500, lambda: self.label_status.configure(text="Successfully installed pynput!", fg="#34d399"))
                self.root.after(600, self.show_success_state)
            else:
                raise Exception("Import check failed post-installation.")
        except Exception as e:
            self.root.after(0, lambda: self.label_status.configure(text="Installation failed. Check internet.", fg="#ef4444"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Could not automatically install dependencies:\n{e}\n\nPlease try running manually:\npip install pynput"))
            sys.exit(1)

    def show_success_state(self):
        if self.ok_button is None:
            self.ok_button = tk.Button(
                self.root, 
                text="pynput loaded! [OK]", 
                bg="#a855f7", 
                fg="#ffffff", 
                activebackground="#c084fc", 
                activeforeground="#ffffff",
                bd=0, 
                padx=15, 
                pady=6, 
                cursor="hand2",
                command=self.complete_loading,
                font=("Segoe UI", 9, "bold")
            )
            self.ok_button.pack(pady=10)

    def complete_loading(self):
        self.root.destroy()
        self.on_success()


class TinyTaskDarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Apex Macro")
        self.root.geometry("360x95")
        self.root.configure(bg="#121212")
        self.root.attributes("-topmost", True)  # Keep on top of other windows
        
        # Ensure clean exit
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

        # Advanced App State Variables
        self.recording_events = []
        self.is_recording = False
        self.is_playing = False
        self.start_time = 0
        self.stop_requested = False
        self.pref_win = None
        
        # Prefs / Customization Defaults
        self.play_speed = 1.0       # Speed multiplier
        self.play_loops = 1         # Loops (0 = infinite)
        self.loop_delay = 0.0       # Seconds delay between loops
        self.randomization_pct = 0  # Random humanize fluctuation % (0-50%)
        
        # Action Filters
        self.filter_clicks = True
        self.filter_movements = True
        self.filter_keyboard = True

        # Custom Hotkey Settings
        self.hotkey_record_str = "F8"
        self.hotkey_play_str = "F12"
        self.hotkey_stop_str = "F6"  # Changed from ESC to F6 to fit user requirement

        # Active Listeners
        self.mouse_listener = None
        self.keyboard_listener = None
        self.global_hotkey_listener = None
        
        # Initialize Controllers
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()

        # Track key/button press times to ensure no immediate virtual releases (fixes click issues)
        self.last_press_times = {}

        # Build UI & Start Up
        self.setup_ui()
        self.apply_dark_title_bar()
        self.start_global_hotkey_listener()
        
        # Record button neon pulsing indicator loop
        self.pulse_state = True
        self.pulse_loop()

    def apply_dark_title_bar(self):
        """Forces the standard Windows title bar to render in native dark mode."""
        self.root.update()
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                if hwnd == 0:
                    hwnd = self.root.winfo_id()
                
                rendering_policy = ctypes.c_int(1)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(rendering_policy), ctypes.sizeof(rendering_policy))
            except Exception:
                pass

    def setup_ui(self):
        # Main Tool Bar
        self.tool_bar = tk.Frame(self.root, bg="#121212")
        self.tool_bar.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Buttons config (Width: 42, Height: 42)
        self.buttons = {}
        button_specs = [
            ("Open", self.draw_open_icon, self.on_open),
            ("Save", self.draw_save_icon, self.on_save),
            ("Rec", self.draw_rec_icon, self.toggle_recording),
            ("Play", self.draw_play_icon, self.toggle_playback),
            (".exe", self.draw_exe_icon, self.on_compile),
            ("Prefs", self.draw_prefs_icon, self.on_prefs)
        ]

        for name, draw_fn, cmd in button_specs:
            btn_frame = tk.Frame(self.tool_bar, bg="#121212")
            btn_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            canvas = tk.Canvas(btn_frame, width=42, height=42, bg="#121212", highlightthickness=0, cursor="hand2")
            canvas.pack(pady=1)
            
            lbl = tk.Label(btn_frame, text=name, fg="#9ca3af", bg="#121212", font=("Segoe UI", 7))
            lbl.pack()

            canvas.bind("<Enter>", lambda e, c=canvas, l=lbl: self.on_button_hover(c, l, True))
            canvas.bind("<Leave>", lambda e, c=canvas, l=lbl: self.on_button_hover(c, l, False))
            canvas.bind("<Button-1>", lambda e, c=cmd: c())

            self.buttons[name] = (canvas, lbl)
            draw_fn(canvas, False)

        # Status Bar
        self.status_bar = tk.Label(
            self.root, 
            text=f"Ready  |  {self.hotkey_record_str}: Rec  |  {self.hotkey_play_str}: Play  |  {self.hotkey_stop_str}: Stop", 
            fg="#6b7280", 
            bg="#0b0b0b", 
            font=("Segoe UI", 7), 
            anchor="w", 
            padx=8,
            pady=2
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    # --- CANVAS VECTOR ART ---
    def draw_open_icon(self, canvas, hover):
        canvas.delete("all")
        bg_col = "#262626" if hover else "#121212"
        canvas.create_rectangle(0, 0, 42, 42, fill=bg_col, outline="")
        color = "#60a5fa" if hover else "#9ca3af"
        canvas.create_polygon([6,10, 15,10, 19,14, 34,14, 34,32, 6,32], fill="", outline=color, width=2)
        canvas.create_line(20, 26, 20, 18, fill=color, width=2)
        canvas.create_polygon([17,21, 20,18, 23,21], fill=color)

    def draw_save_icon(self, canvas, hover):
        canvas.delete("all")
        bg_col = "#262626" if hover else "#121212"
        canvas.create_rectangle(0, 0, 42, 42, fill=bg_col, outline="")
        color = "#a855f7" if hover else "#9ca3af"
        canvas.create_polygon([8,8, 28,8, 34,14, 34,34, 8,34], fill="", outline=color, width=2)
        canvas.create_rectangle(14, 22, 28, 34, outline=color, width=1)
        canvas.create_rectangle(14, 8, 24, 16, fill=color, outline="")

    def draw_rec_icon(self, canvas, hover):
        canvas.delete("all")
        bg_col = "#262626" if hover else "#121212"
        canvas.create_rectangle(0, 0, 42, 42, fill=bg_col, outline="")
        if self.is_recording:
            color = "#ef4444" if self.pulse_state else "#991b1b"
        else:
            color = "#f87171" if hover else "#ef4444"
        canvas.create_oval(11, 11, 31, 31, fill=color, outline="")

    def draw_play_icon(self, canvas, hover):
        canvas.delete("all")
        bg_col = "#262626" if hover else "#121212"
        canvas.create_rectangle(0, 0, 42, 42, fill=bg_col, outline="")
        if self.is_playing:
            color = "#f59e0b" if hover else "#d97706"
            canvas.create_rectangle(12, 12, 30, 30, fill=color, outline="")
        else:
            color = "#34d399" if hover else "#10b981"
            canvas.create_polygon([14,10, 32,21, 14,32], fill=color, outline="")

    def draw_exe_icon(self, canvas, hover):
        canvas.delete("all")
        bg_col = "#262626" if hover else "#121212"
        canvas.create_rectangle(0, 0, 42, 42, fill=bg_col, outline="")
        color = "#38bdf8" if hover else "#9ca3af"
        canvas.create_line(21, 8, 21, 26, fill=color, width=2)
        canvas.create_polygon([16,21, 21,26, 26,21], fill=color)
        canvas.create_line(12, 32, 30, 32, fill=color, width=2)

    def draw_prefs_icon(self, canvas, hover):
        canvas.delete("all")
        bg_col = "#262626" if hover else "#121212"
        canvas.create_rectangle(0, 0, 42, 42, fill=bg_col, outline="")
        color = "#e2e8f0" if hover else "#9ca3af"
        canvas.create_line(12, 30, 26, 16, fill=color, width=3)
        canvas.create_oval(24, 12, 32, 20, outline=color, width=2)
        canvas.create_line(30, 12, 12, 30, fill="#f87171" if hover else color, width=2)
        canvas.create_rectangle(8, 28, 14, 34, fill=color, outline="")

    def on_button_hover(self, canvas, label, hover):
        name = label.cget("text")
        label.configure(fg="#ffffff" if hover else "#9ca3af")
        if name == "Open": self.draw_open_icon(canvas, hover)
        elif name == "Save": self.draw_save_icon(canvas, hover)
        elif name == "Rec": self.draw_rec_icon(canvas, hover)
        elif name == "Play": self.draw_play_icon(canvas, hover)
        elif name == ".exe": self.draw_exe_icon(canvas, hover)
        elif name == "Prefs": self.draw_prefs_icon(canvas, hover)

    def pulse_loop(self):
        if self.is_recording:
            self.pulse_state = not self.pulse_state
            rec_canvas, _ = self.buttons["Rec"]
            self.draw_rec_icon(rec_canvas, False)
        self.root.after(500, self.pulse_loop)

    def update_status(self, text, color="#6b7280"):
        self.status_bar.configure(text=text, fg=color)
        self.root.update_idletasks()

    # --- INTELLIGENT BOUNDING BOX FILTER ---
    def is_inside_gui(self, x, y):
        """Checks if a given coordinate is inside the main window or preferences modal."""
        try:
            rx = self.root.winfo_rootx()
            ry = self.root.winfo_rooty()
            rw = self.root.winfo_width()
            rh = self.root.winfo_height()
            if rx <= x <= (rx + rw) and ry <= y <= (ry + rh):
                return True
        except Exception:
            pass

        if self.pref_win and self.pref_win.winfo_exists():
            try:
                px = self.pref_win.winfo_rootx()
                py = self.pref_win.winfo_rooty()
                pw = self.pref_win.winfo_width()
                ph = self.pref_win.winfo_height()
                if px <= x <= (px + pw) and py <= y <= (py + ph):
                    return True
            except Exception:
                pass
        return False

    # --- RESOLVING KEYBOARD MAPS ---
    def parse_hotkey_to_pynput(self, val_str):
        val = val_str.upper().strip()
        if hasattr(keyboard.Key, val.lower()):
            return getattr(keyboard.Key, val.lower())
        if val == "ESC":
            return keyboard.Key.esc
        if val.startswith("F") and val[1:].isdigit():
            return getattr(keyboard.Key, val.lower())
        return val

    # --- HOTKEY GLOBAL LISTENER ---
    def start_global_hotkey_listener(self):
        if self.global_hotkey_listener:
            self.global_hotkey_listener.stop()

        target_rec = self.parse_hotkey_to_pynput(self.hotkey_record_str)
        target_play = self.parse_hotkey_to_pynput(self.hotkey_play_str)
        target_stop = self.parse_hotkey_to_pynput(self.hotkey_stop_str)

        def on_press(key):
            try:
                matched_key = None
                if isinstance(key, keyboard.Key):
                    matched_key = key
                elif hasattr(key, 'char') and key.char:
                    matched_key = key.char.upper()

                if matched_key == target_rec:
                    self.root.after(10, self.toggle_recording)
                elif matched_key == target_play:
                    self.root.after(10, self.toggle_playback)
                elif matched_key == target_stop and self.is_playing:
                    self.stop_requested = True
            except Exception:
                pass

        self.global_hotkey_listener = keyboard.Listener(on_press=on_press)
        self.global_hotkey_listener.daemon = True
        self.global_hotkey_listener.start()

    # --- RECORD LOGIC ---
    def toggle_recording(self):
        if self.is_playing:
            return
        
        if not self.is_recording:
            self.is_recording = True
            self.recording_events = []
            self.start_time = time.time()
            self.update_status(f"Recording... [{self.hotkey_record_str}] to Stop", "#ef4444")
            
            self.mouse_listener = mouse.Listener(
                on_move=self.record_mouse_move,
                on_click=self.record_mouse_click,
                on_scroll=self.record_mouse_scroll
            )
            self.keyboard_listener = keyboard.Listener(
                on_press=self.record_key_press,
                on_release=self.record_key_release
            )
            
            self.mouse_listener.start()
            self.keyboard_listener.start()
        else:
            self.is_recording = False
            self.update_status(f"Recording Saved! ({len(self.recording_events)} events)", "#34d399")
            
            if self.mouse_listener: self.mouse_listener.stop()
            if self.keyboard_listener: self.keyboard_listener.stop()

        rec_canvas, _ = self.buttons["Rec"]
        self.draw_rec_icon(rec_canvas, False)

    def get_elapsed(self):
        return time.time() - self.start_time

    def record_mouse_move(self, x, y):
        if not self.filter_movements or self.is_inside_gui(x, y):
            return
        self.recording_events.append({
            "t": self.get_elapsed(),
            "type": "m_move",
            "x": x, "y": y
        })

    def record_mouse_click(self, x, y, button, pressed):
        if not self.filter_clicks or self.is_inside_gui(x, y):
            return
        self.recording_events.append({
            "t": self.get_elapsed(),
            "type": "m_click",
            "x": x, "y": y,
            "btn": button.name,
            "pressed": pressed
        })

    def record_mouse_scroll(self, x, y, dx, dy):
        if not self.filter_clicks or self.is_inside_gui(x, y):
            return
        self.recording_events.append({
            "t": self.get_elapsed(),
            "type": "m_scroll",
            "x": x, "y": y,
            "dx": dx, "dy": dy
        })

    def serialize_key(self, key):
        try:
            return key.char
        except AttributeError:
            return str(key)

    def record_key_press(self, key):
        if not self.filter_keyboard:
            return
        target_rec = self.parse_hotkey_to_pynput(self.hotkey_record_str)
        target_play = self.parse_hotkey_to_pynput(self.hotkey_play_str)
        if key == target_rec or key == target_play:
            return
            
        self.recording_events.append({
            "t": self.get_elapsed(),
            "type": "k_press",
            "key": self.serialize_key(key)
        })

    def record_key_release(self, key):
        if not self.filter_keyboard:
            return
        target_rec = self.parse_hotkey_to_pynput(self.hotkey_record_str)
        target_play = self.parse_hotkey_to_pynput(self.hotkey_play_str)
        if key == target_rec or key == target_play:
            return
            
        self.recording_events.append({
            "t": self.get_elapsed(),
            "type": "k_release",
            "key": self.serialize_key(key)
        })

    # --- REPLAY LOGIC ---
    def toggle_playback(self):
        if self.is_recording:
            return
        
        if not self.is_playing:
            if not self.recording_events:
                self.update_status("No recorded macro!", "#ef4444")
                return
            
            self.is_playing = True
            self.stop_requested = False
            play_canvas, _ = self.buttons["Play"]
            self.draw_play_icon(play_canvas, False)
            
            threading.Thread(target=self.playback_thread_proc, daemon=True).start()
        else:
            self.stop_requested = True

    def playback_thread_proc(self):
        try:
            # 1. Minimize the macro window immediately so game window gets direct active input focus
            self.root.after(0, self.root.iconify)
            time.sleep(0.3) # Settle buffer for Windows OS window minimization transitions

            loops_run = 0
            import random
            
            while self.is_playing and not self.stop_requested:
                if self.play_loops > 0 and loops_run >= self.play_loops:
                    break
                
                # Check for Delay between iterations
                if loops_run > 0 and self.loop_delay > 0:
                    self.update_status(f"Waiting delay ({self.loop_delay}s)...", "#a855f7")
                    end_delay_time = time.time() + self.loop_delay
                    while time.time() < end_delay_time:
                        if self.stop_requested:
                            break
                        time.sleep(0.05)
                        
                if self.stop_requested:
                    break

                loops_run += 1
                loop_info = f" (Loop {loops_run}/{self.play_loops})" if self.play_loops > 0 else " (Looping...)"
                self.update_status(f"Playing macro{loop_info}... [{self.hotkey_stop_str}] to Stop", "#34d399")
                
                start_exec = time.time()
                self.last_press_times.clear()
                
                for event in self.recording_events:
                    if self.stop_requested:
                        break
                    
                    delay_factor = 1.0
                    if self.randomization_pct > 0:
                        fluc = (self.randomization_pct / 100.0)
                        delay_factor += random.uniform(-fluc, fluc)

                    target_elapsed = (event["t"] / self.play_speed) * delay_factor
                    actual_elapsed = time.time() - start_exec
                    delay = target_elapsed - actual_elapsed
                    
                    if delay > 0:
                        time.sleep(delay)

                    self.execute_event(event)
            
            if self.stop_requested:
                self.update_status("Replay Stopped!", "#f59e0b")
            else:
                self.update_status("Replay Finished!", "#10b981")
                
        except Exception as e:
            self.update_status("Replay Exception!", "#ef4444")
            print(f"Exception: {e}")
        finally:
            self.release_all_inputs()
            self.is_playing = False
            
            # 2. Restore and bring macro back to shown view
            self.root.after(0, self.root.deiconify)
            self.root.after(10, lambda: self.root.attributes("-topmost", True))
            self.root.after(15, self.reset_play_button_ui)

    def reset_play_button_ui(self):
        play_canvas, _ = self.buttons["Play"]
        self.draw_play_icon(play_canvas, False)

    def execute_event(self, event):
        etype = event["type"]
        if etype == "m_move":
            self.mouse_controller.position = (event["x"], event["y"])
            time.sleep(0.005)
        elif etype == "m_click":
            self.mouse_controller.position = (event["x"], event["y"])
            time.sleep(0.010)
            
            btn = getattr(mouse.Button, event["btn"])
            if event["pressed"]:
                self.mouse_controller.press(btn)
                self.last_press_times[event["btn"]] = time.time()
            else:
                press_time = self.last_press_times.get(event["btn"], 0)
                elapsed = time.time() - press_time
                min_hold_duration = 0.045
                if elapsed < min_hold_duration:
                    time.sleep(min_hold_duration - elapsed)
                
                self.mouse_controller.release(btn)
        elif etype == "m_scroll":
            self.mouse_controller.position = (event["x"], event["y"])
            self.mouse_controller.scroll(event["dx"], event["dy"])
        elif etype in ("k_press", "k_release"):
            key_val = event["key"]
            if key_val.startswith("Key."):
                k_name = key_val.split(".")[1]
                key_obj = getattr(keyboard.Key, k_name, None)
            else:
                key_obj = key_val

            if key_obj:
                try:
                    if etype == "k_press":
                        self.keyboard_controller.press(key_obj)
                    else:
                        self.keyboard_controller.release(key_obj)
                except Exception:
                    pass

    def release_all_inputs(self):
        """Safely sweeps and releases mouse/key triggers to prevent stuck button states."""
        try:
            for btn_name in ["left", "right", "middle"]:
                btn = getattr(mouse.Button, btn_name, None)
                if btn:
                    self.mouse_controller.release(btn)
        except Exception:
            pass
        try:
            for key in [keyboard.Key.shift, keyboard.Key.ctrl, keyboard.Key.alt]:
                self.keyboard_controller.release(key)
        except Exception:
            pass

    # --- SAVE / LOAD DATA ---
    def on_save(self):
        if not self.recording_events:
            messagebox.showwarning("Empty Project", "Nothing recorded to save!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Apex Macro JSON", "*.json"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w") as f:
                    json.dump(self.recording_events, f, indent=2)
                self.update_status("Project Saved!", "#10b981")
            except Exception as e:
                messagebox.showerror("Save Failure", f"Failed to save:\n{e}")

    def on_open(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Apex Macro JSON", "*.json"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "r") as f:
                    self.recording_events = json.load(f)
                self.update_status(f"Imported ({len(self.recording_events)} events)", "#10b981")
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to read:\n{e}")

    # --- EXPORT TO STANDALONE RUNNABLE BINARY (.EXE) ---
    def on_compile(self):
        if not self.recording_events:
            messagebox.showwarning("Compile Action", "Record or load a macro sequence first!")
            return

        out_exe_path = filedialog.asksaveasfilename(
            defaultextension=".exe",
            filetypes=[("Executable Files", "*.exe")]
        )
        if not out_exe_path:
            return

        self.update_status("Compiling standalone EXE...", "#38bdf8")
        pyinstaller_exists = shutil.which("pyinstaller") is not None

        # Prepare self-contained source
        macro_payload = json.dumps(self.recording_events)
        runner_code = f"""# Compact Standalone Executable
import time
import json
import sys
import random
from pynput import mouse, keyboard

EVENTS = {macro_payload}
SPEED = {self.play_speed}
LOOPS = {self.play_loops}
DELAY = {self.loop_delay}
RAND = {self.randomization_pct}

def play_macro():
    mouse_ctrl = mouse.Controller()
    kb_ctrl = keyboard.Controller()
    
    stop_execution = False
    def on_press(key):
        nonlocal stop_execution
        if key == keyboard.Key.{self.hotkey_stop_str.lower()}:
            stop_execution = True

    listener = keyboard.Listener(on_press=on_press)
    listener.daemon = True
    listener.start()

    last_press_times = {{}}
    run_count = 0
    while True:
        if LOOPS > 0 and run_count >= LOOPS:
            break
        if stop_execution:
            break
            
        if run_count > 0 and DELAY > 0:
            time.sleep(DELAY)
            
        run_count += 1
        start_time = time.time()
        last_press_times.clear()
        
        for event in EVENTS:
            if stop_execution:
                break
                
            delay_factor = 1.0
            if RAND > 0:
                delay_factor += random.uniform(-(RAND/100.0), (RAND/100.0))

            target_elapsed = (event["t"] / SPEED) * delay_factor
            actual_elapsed = time.time() - start_time
            delay_val = target_elapsed - actual_elapsed
            
            if delay_val > 0:
                time.sleep(delay_val)
                
            etype = event["type"]
            if etype == "m_move":
                mouse_ctrl.position = (event["x"], event["y"])
                time.sleep(0.005)
            elif etype == "m_click":
                mouse_ctrl.position = (event["x"], event["y"])
                time.sleep(0.010)
                btn = getattr(mouse.Button, event["btn"])
                if event["pressed"]:
                    mouse_ctrl.press(btn)
                    last_press_times[event["btn"]] = time.time()
                else:
                    press_time = last_press_times.get(event["btn"], 0)
                    elapsed = time.time() - press_time
                    min_hold = 0.045
                    if elapsed < min_hold:
                        time.sleep(min_hold - elapsed)
                    mouse_ctrl.release(btn)
            elif etype == "m_scroll":
                mouse_ctrl.position = (event["x"], event["y"])
                mouse_ctrl.scroll(event["dx"], event["dy"])
            elif etype in ("k_press", "k_release"):
                key_val = event["key"]
                if key_val.startswith("Key."):
                    k_name = key_val.split(".")[1]
                    key_obj = getattr(keyboard.Key, k_name, None)
                else:
                    key_obj = key_val
                if key_obj:
                    try:
                        if etype == "k_press":
                            kb_ctrl.press(key_obj)
                        else:
                            kb_ctrl.release(key_obj)
                    except Exception:
                        pass
    
    # Safe cleanup release of active physical sweeps on runner completion
    try:
        for b_name in ["left", "right", "middle"]:
            b_obj = getattr(mouse.Button, b_name, None)
            if b_obj: mouse_ctrl.release(b_obj)
    except Exception: pass

if __name__ == "__main__":
    play_macro()
"""
        
        target_dir = os.path.dirname(out_exe_path)
        base_name = os.path.splitext(os.path.basename(out_exe_path))[0]
        temp_py_path = os.path.join(target_dir, f"{base_name}_standalone.py")
        
        try:
            with open(temp_py_path, "w", encoding="utf-8") as f:
                f.write(runner_code)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to draft script file:\n{e}")
            self.update_status("Drafting failed!", "#ef4444")
            return

        if not pyinstaller_exists:
            messagebox.showinfo(
                "Automation Complete (Local Build Necessary)",
                f"We saved your fully functional standalone macro script at:\n{temp_py_path}\n\n"
                f"To turn it into an EXE manually, run:\n"
                f"pip install pyinstaller pynput\n"
                f"pyinstaller --onefile --noconsole \"{temp_py_path}\""
            )
            self.update_status("Runner template saved!", "#f59e0b")
            return

        def build_exe_thread():
            try:
                cmd = [
                    "pyinstaller",
                    "--onefile",
                    "--noconsole",
                    "--distpath", target_dir,
                    "--workpath", os.path.join(target_dir, "build"),
                    "--specpath", target_dir,
                    temp_py_path
                ]
                
                # Suppress command prompt flashes
                startupinfo = None
                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                subprocess.run(cmd, startupinfo=startupinfo, check=True)
                
                spec_file = os.path.join(target_dir, f"{base_name}_standalone.spec")
                build_dir = os.path.join(target_dir, "build")
                
                if os.path.exists(spec_file): os.remove(spec_file)
                if os.path.exists(build_dir): shutil.rmtree(build_dir)
                if os.path.exists(temp_py_path): os.remove(temp_py_path)
                
                generated_exe = os.path.join(target_dir, f"{base_name}_standalone.exe")
                if os.path.exists(generated_exe):
                    if os.path.exists(out_exe_path): os.remove(out_exe_path)
                    os.rename(generated_exe, out_exe_path)

                self.root.after(10, lambda: messagebox.showinfo("Build Success", f"Your executable is ready:\n{out_exe_path}"))
                self.root.after(10, lambda: self.update_status("Execution build ready!", "#10b981"))
            except Exception as ex:
                self.root.after(10, lambda: messagebox.showerror("Builder Exception", f"Compilation failed:\n{ex}"))
                self.root.after(10, lambda: self.update_status("Compiling failed!", "#ef4444"))

        threading.Thread(target=build_exe_thread, daemon=True).start()

    # --- ADVANCED PREFERENCES PANEL ---
    def on_prefs(self):
        self.pref_win = tk.Toplevel(self.root)
        self.pref_win.title("Preferences & Customization")
        self.pref_win.geometry("450x300")
        self.pref_win.configure(bg="#111111")
        self.pref_win.grab_set()
        
        mx = self.root.winfo_x() - 45
        my = self.root.winfo_y() - 110
        self.pref_win.geometry(f"+{mx if mx > 0 else 10}+{my if my > 0 else 10}")

        main_frame = tk.Frame(self.pref_win, bg="#111111", padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ----------------- SECTION 1: TIMINGS & LOOPS -----------------
        section_1 = tk.LabelFrame(main_frame, text=" Timing & Loops ", bg="#111111", fg="#a855f7", font=("Segoe UI", 9, "bold"), padx=10, pady=8)
        section_1.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Speed Multiplier
        tk.Label(section_1, text="Replay Speed:", fg="#e5e7eb", bg="#111111").grid(row=0, column=0, sticky="w", pady=4)
        speed_var = tk.StringVar(value=str(self.play_speed))
        speed_combo = tk.OptionMenu(section_1, speed_var, "0.5", "1.0", "1.5", "2.0", "5.0", "10.0")
        speed_combo.configure(bg="#1f1f1f", fg="#ffffff", activebackground="#2a2a2a", bd=0, highlightthickness=0)
        speed_combo["menu"].configure(bg="#1f1f1f", fg="#ffffff", selectcolor="#a855f7")
        speed_combo.grid(row=0, column=1, sticky="w", padx=10)

        # Loop Counts
        tk.Label(section_1, text="Loops (0 = ∞):", fg="#e5e7eb", bg="#111111").grid(row=0, column=2, sticky="w", pady=4)
        loops_entry = tk.Entry(section_1, width=8, bg="#1f1f1f", fg="#ffffff", insertbackground="#ffffff", bd=0, highlightthickness=1, highlightcolor="#a855f7")
        loops_entry.insert(0, str(self.play_loops))
        loops_entry.grid(row=0, column=3, sticky="w", padx=10)

        # Loop delay
        tk.Label(section_1, text="Delay Between Loops (s):", fg="#e5e7eb", bg="#111111").grid(row=1, column=0, sticky="w", pady=4)
        delay_entry = tk.Entry(section_1, width=8, bg="#1f1f1f", fg="#ffffff", insertbackground="#ffffff", bd=0, highlightthickness=1, highlightcolor="#a855f7")
        delay_entry.insert(0, str(self.loop_delay))
        delay_entry.grid(row=1, column=1, sticky="w", padx=10)

        # Timing Humanizer / Randomization
        tk.Label(section_1, text="Humanize Delay fluctuation:", fg="#e5e7eb", bg="#111111").grid(row=1, column=2, sticky="w", pady=4)
        rand_var = tk.StringVar(value=str(self.randomization_pct))
        rand_combo = tk.OptionMenu(section_1, rand_var, "0", "5", "10", "15", "25", "40")
        rand_combo.configure(bg="#1f1f1f", fg="#ffffff", activebackground="#2a2a2a", bd=0, highlightthickness=0)
        rand_combo["menu"].configure(bg="#1f1f1f", fg="#ffffff", selectcolor="#a855f7")
        rand_combo.grid(row=1, column=3, sticky="w", padx=10)

        # ----------------- SECTION 2: FILTERS -----------------
        section_2 = tk.LabelFrame(main_frame, text=" Active Action Filters ", bg="#111111", fg="#a855f7", font=("Segoe UI", 9, "bold"), padx=10, pady=8)
        section_2.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=(0, 10))

        # Checkboxes
        chk_clicks = tk.BooleanVar(value=self.filter_clicks)
        tk.Checkbutton(section_2, text="Record Mouse Clicks", variable=chk_clicks, bg="#111111", fg="#e5e7eb", selectcolor="#111111", activebackground="#111111", activeforeground="#ffffff").pack(anchor="w", pady=2)

        chk_moves = tk.BooleanVar(value=self.filter_movements)
        tk.Checkbutton(section_2, text="Record Mouse Movement", variable=chk_moves, bg="#111111", fg="#e5e7eb", selectcolor="#111111", activebackground="#111111", activeforeground="#ffffff").pack(anchor="w", pady=2)

        chk_keys = tk.BooleanVar(value=self.filter_keyboard)
        tk.Checkbutton(section_2, text="Record Keyboard Inputs", variable=chk_keys, bg="#111111", fg="#e5e7eb", selectcolor="#111111", activebackground="#111111", activeforeground="#ffffff").pack(anchor="w", pady=2)

        # ----------------- SECTION 3: KEYBOARD SHORTCUTS -----------------
        section_3 = tk.LabelFrame(main_frame, text=" Custom Shortcuts ", bg="#111111", fg="#a855f7", font=("Segoe UI", 9, "bold"), padx=10, pady=8)
        section_3.grid(row=1, column=1, sticky="nsew", padx=(5, 0), pady=(0, 10))

        # Hotkeys strings
        tk.Label(section_3, text="Record/Stop:", fg="#e5e7eb", bg="#111111").grid(row=0, column=0, sticky="w", pady=3)
        hk_rec_entry = tk.Entry(section_3, width=8, bg="#1f1f1f", fg="#ffffff", insertbackground="#ffffff", bd=0, highlightthickness=1, highlightcolor="#a855f7")
        hk_rec_entry.insert(0, self.hotkey_record_str)
        hk_rec_entry.grid(row=0, column=1, sticky="e", padx=5)

        tk.Label(section_3, text="Play Macro:", fg="#e5e7eb", bg="#111111").grid(row=1, column=0, sticky="w", pady=3)
        hk_play_entry = tk.Entry(section_3, width=8, bg="#1f1f1f", fg="#ffffff", insertbackground="#ffffff", bd=0, highlightthickness=1, highlightcolor="#a855f7")
        hk_play_entry.insert(0, self.hotkey_play_str)
        hk_play_entry.grid(row=1, column=1, sticky="e", padx=5)

        tk.Label(section_3, text="Emergency Stop:", fg="#e5e7eb", bg="#111111").grid(row=2, column=0, sticky="w", pady=3)
        hk_stop_entry = tk.Entry(section_3, width=8, bg="#1f1f1f", fg="#ffffff", insertbackground="#ffffff", bd=0, highlightthickness=1, highlightcolor="#a855f7")
        hk_stop_entry.insert(0, self.hotkey_stop_str)
        hk_stop_entry.grid(row=2, column=1, sticky="e", padx=5)

        # ----------------- SAVE BUTTON -----------------
        def save_and_apply():
            try:
                # Timings & loops validate
                self.play_speed = float(speed_var.get())
                self.play_loops = int(loops_entry.get())
                self.loop_delay = float(delay_entry.get())
                self.randomization_pct = int(rand_var.get())

                # Filters apply
                self.filter_clicks = chk_clicks.get()
                self.filter_movements = chk_moves.get()
                self.filter_keyboard = chk_keys.get()

                # Hotkeys apply
                self.hotkey_record_str = hk_rec_entry.get().upper().strip()
                self.hotkey_play_str = hk_play_entry.get().upper().strip()
                self.hotkey_stop_str = hk_stop_entry.get().upper().strip()

                # Reinitialize Hotkeys
                self.start_global_hotkey_listener()

                self.update_status("Preferences & Customizations Saved!", "#a855f7")
                self.pref_win.destroy()
            except ValueError:
                messagebox.showerror("Validation Error", "Please input valid numbers in Preferences!", parent=self.pref_win)

        btn_apply = tk.Button(
            main_frame, text="Apply & Save Configuration", bg="#a855f7", fg="#ffffff", activebackground="#c084fc", bd=0,
            padx=20, pady=8, cursor="hand2", command=save_and_apply, font=("Segoe UI", 9, "bold")
        )
        btn_apply.grid(row=2, column=0, columnspan=2, pady=(10, 0))

    def quit_app(self):
        if self.global_hotkey_listener: self.global_hotkey_listener.stop()
        if self.mouse_listener: self.mouse_listener.stop()
        if self.keyboard_listener: self.keyboard_listener.stop()
        self.root.destroy()


def launch_main_app():
    root = tk.Tk()
    app = TinyTaskDarkApp(root)
    # Center app window
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws / 2) - (360 / 2)
    y = (hs / 2) - (95 / 2)
    root.geometry(f"+{int(x)}+{int(y)}")
    root.mainloop()

if __name__ == "__main__":
    if try_import_pynput():
        def prompt_loaded():
            confirm = tk.Tk()
            confirm.withdraw()
            messagebox.showinfo("Apex Macro", "pynput loaded!")
            confirm.destroy()
            launch_main_app()
        prompt_loaded()
    else:
        DependencyLoader(on_success_callback=launch_main_app)