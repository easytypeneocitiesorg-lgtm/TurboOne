import time
import threading
import tkinter as tk
import vgamepad as vg
import XInput

# --- GLOBAL STATE ---
active_macros = {}
running = True

output_state = {
    "buttons": 0,
    "LT": 0,
    "RT": 0
}

BUTTON_MAP = {
    "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    "LB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    "RB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    "UP": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    "DOWN": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    "LEFT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    "RIGHT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
    "LS": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    "RS": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    "START": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    "BACK": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK
}

# --- THEME COLORS ---
BG_COLOR = "#121212"
PANEL_COLOR = "#1e1e1e"
BTN_NORMAL = "#2a2a2a" 
BTN_GLOW = "#00e5ff"   # Cyan glow for active input
TEXT_COLOR = "#ffffff"
TURBO_OFF_BG = "#333333"
TURBO_ON_BG = "#ff3b30" 

# Canvas shapes dictionary to update colors
controller_shapes = {}

# --- BACKGROUND THREAD LOGIC ---
def gamepad_loop():
    global running
    
    connected = XInput.get_connected()
    if not any(connected):
        print("No physical controller detected!")
        return

    controller_index = connected.index(True)
    
    try:
        virtual_pad = vg.VX360Gamepad()
    except Exception as e:
        print(f"Error creating virtual gamepad: {e}")
        return

    try:
        while running:
            state = XInput.get_state(controller_index)
            
            virtual_buttons = state.Gamepad.wButtons
            virtual_lt = state.Gamepad.bLeftTrigger
            virtual_rt = state.Gamepad.bRightTrigger
            
            current_time_ms = time.perf_counter() * 1000

            # Process Standard Buttons
            for btn_name, bitmask in BUTTON_MAP.items():
                if btn_name in active_macros:
                    delay = active_macros[btn_name]
                    spam_on = (current_time_ms % delay) < (delay / 2)
                    
                    if (virtual_buttons & bitmask): 
                        if not spam_on:
                            virtual_buttons &= ~bitmask
            
            # Process Triggers
            if "LT" in active_macros and virtual_lt > 30:
                delay = active_macros["LT"]
                spam_on = (current_time_ms % delay) < (delay / 2)
                virtual_lt = 255 if spam_on else 0
                
            if "RT" in active_macros and virtual_rt > 30:
                delay = active_macros["RT"]
                spam_on = (current_time_ms % delay) < (delay / 2)
                virtual_rt = 255 if spam_on else 0

            # Update global state for the visual calibrator
            output_state["buttons"] = virtual_buttons
            output_state["LT"] = virtual_lt
            output_state["RT"] = virtual_rt

            virtual_pad.report.wButtons = virtual_buttons
            virtual_pad.left_joystick(x_value=state.Gamepad.sThumbLX, y_value=state.Gamepad.sThumbLY)
            virtual_pad.right_joystick(x_value=state.Gamepad.sThumbRX, y_value=state.Gamepad.sThumbRY)
            virtual_pad.left_trigger(value=virtual_lt)
            virtual_pad.right_trigger(value=virtual_rt)
            
            virtual_pad.update()
            time.sleep(0.001)

    except Exception as e:
        print(f"Controller Error: {e}")
    finally:
        virtual_pad.reset()
        virtual_pad.update()


# --- UI LOGIC ---
def toggle_macro(btn_name, btn_widget, entry_var, entry_widget):
    if btn_name in active_macros:
        # Turn OFF
        del active_macros[btn_name]
        btn_widget.config(bg=TURBO_OFF_BG, text="OFF", fg="#aaaaaa")
        entry_widget.config(state=tk.NORMAL) 
    else:
        # Turn ON
        try:
            delay = float(entry_var.get())
            if delay <= 0:
                delay = 25 
        except ValueError:
            delay = 25
            entry_var.set("25")
            
        active_macros[btn_name] = delay
        btn_widget.config(bg=TURBO_ON_BG, text="TURBO", fg="white")
        entry_widget.config(state=tk.DISABLED)

def poll_controller_state(root, canvas):
    if not running: 
        return
    
    b_state = output_state["buttons"]
    lt_state = output_state["LT"]
    rt_state = output_state["RT"]
    
    for btn_name, shape_id in controller_shapes.items():
        if btn_name == "LT":
            is_active = lt_state > 30
        elif btn_name == "RT":
            is_active = rt_state > 30
        else:
            is_active = bool(b_state & BUTTON_MAP[btn_name])
            
        color = BTN_GLOW if is_active else BTN_NORMAL
        canvas.itemconfig(shape_id, fill=color)
        
    root.after(15, poll_controller_state, root, canvas)

def on_closing(root):
    global running
    running = False
    time.sleep(0.1)
    root.destroy()


# --- GUI DRAWING: BUTTON LAYOUT MATRIX ---
def draw_controller(canvas):
    """Draws a clean, modern button matrix layout representing the controller topology."""
    
    PANEL_BG = "#181818"
    ACCENT = "#383838"
    TEXT = "#aaaaaa"

    # Background panel container for the layout
    canvas.create_rounded_rect = lambda x1, y1, x2, y2, r, **kwargs: canvas.create_polygon(
        (x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2, x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1), 
        smooth=True, **kwargs
    )
    
    canvas.create_rounded_rect(20, 20, 380, 330, 15, fill=PANEL_BG, outline=ACCENT, width=2)

    # --- Top Row: Triggers & Bumpers ---
    # LT / LB (Left)
    controller_shapes["LT"] = canvas.create_rectangle(45, 40, 105, 75, fill=BTN_NORMAL, outline=ACCENT, width=2)
    canvas.create_text(75, 57, text="LT", fill=TEXT, font=("Arial", 9, "bold"))
    
    controller_shapes["LB"] = canvas.create_rectangle(115, 40, 175, 75, fill=BTN_NORMAL, outline=ACCENT, width=2)
    canvas.create_text(145, 57, text="LB", fill=TEXT, font=("Arial", 9, "bold"))

    # RT / RB (Right)
    controller_shapes["RB"] = canvas.create_rectangle(225, 40, 285, 75, fill=BTN_NORMAL, outline=ACCENT, width=2)
    canvas.create_text(255, 57, text="RB", fill=TEXT, font=("Arial", 9, "bold"))
    
    controller_shapes["RT"] = canvas.create_rectangle(295, 40, 355, 75, fill=BTN_NORMAL, outline=ACCENT, width=2)
    canvas.create_text(325, 57, text="RT", fill=TEXT, font=("Arial", 9, "bold"))

    # --- Middle Section: Joysticks & Center Buttons ---
    # Left Stick (LS)
    ls_x, ls_y = 90, 140
    canvas.create_oval(ls_x-32, ls_y-32, ls_x+32, ls_y+32, fill="#111111", outline=ACCENT, width=2)
    controller_shapes["LS"] = canvas.create_oval(ls_x-24, ls_y-24, ls_x+24, ls_y+24, fill=BTN_NORMAL, outline="#444444", width=2)
    canvas.create_text(ls_x, ls_y, text="LS", fill=TEXT, font=("Arial", 9, "bold"))

    # Center: Back & Start
    back_x, back_y = 170, 120
    controller_shapes["BACK"] = canvas.create_rectangle(back_x-22, back_y-12, back_x+22, back_y+12, fill=BTN_NORMAL, outline=ACCENT, width=2)
    canvas.create_text(back_x, back_y, text="BACK", fill=TEXT, font=("Arial", 8, "bold"))

    start_x, start_y = 230, 120
    controller_shapes["START"] = canvas.create_rectangle(start_x-22, start_y-12, start_x+22, start_y+12, fill=BTN_NORMAL, outline=ACCENT, width=2)
    canvas.create_text(start_x, start_y, text="START", fill=TEXT, font=("Arial", 8, "bold"))

    # Right Stick (RS) - Moved right and down slightly
    rs_x, rs_y = 240, 245
    canvas.create_oval(rs_x-32, rs_y-32, rs_x+32, rs_y+32, fill="#111111", outline=ACCENT, width=2)
    controller_shapes["RS"] = canvas.create_oval(rs_x-24, rs_y-24, rs_x+24, rs_y+24, fill=BTN_NORMAL, outline="#444444", width=2)
    canvas.create_text(rs_x, rs_y, text="RS", fill=TEXT, font=("Arial", 9, "bold"))


    # --- Lower Section: D-Pad (Left) & Face Buttons (Right) ---
    # D-Pad Layout (Cross format)
    dp_x, dp_y = 90, 245
    controller_shapes["UP"] = canvas.create_rectangle(dp_x-15, dp_y-42, dp_x+15, dp_y-14, fill=BTN_NORMAL, outline=ACCENT, width=2)
    controller_shapes["DOWN"] = canvas.create_rectangle(dp_x-15, dp_y+14, dp_x+15, dp_y+42, fill=BTN_NORMAL, outline=ACCENT, width=2)
    controller_shapes["LEFT"] = canvas.create_rectangle(dp_x-42, dp_y-15, dp_x-14, dp_y+15, fill=BTN_NORMAL, outline=ACCENT, width=2)
    controller_shapes["RIGHT"] = canvas.create_rectangle(dp_x+14, dp_y-15, dp_x+42, dp_y+15, fill=BTN_NORMAL, outline=ACCENT, width=2)
    canvas.create_text(dp_x, dp_y, text="DPAD", fill="#666666", font=("Arial", 7, "bold"))


    # Face Buttons Layout (Diamond format: Y top, A bottom, X left, B right) - Compact & moved up
    fb_x, fb_y = 300, 180
    btn_size = 18
    offset = 35
    
    # Y Button (Top)
    controller_shapes["Y"] = canvas.create_oval(fb_x-btn_size, fb_y-offset-btn_size, fb_x+btn_size, fb_y-offset+btn_size, fill=BTN_NORMAL, outline=ACCENT, width=2)
    canvas.create_text(fb_x, fb_y-offset, text="Y", fill=TEXT, font=("Arial", 8, "bold"))

    # A Button (Bottom)
    controller_shapes["A"] = canvas.create_oval(fb_x-btn_size, fb_y+offset-btn_size, fb_x+btn_size, fb_y+offset+btn_size, fill=BTN_NORMAL, outline=ACCENT, width=2)
    canvas.create_text(fb_x, fb_y+offset, text="A", fill=TEXT, font=("Arial", 8, "bold"))

    # X Button (Left)
    controller_shapes["X"] = canvas.create_oval(fb_x-offset-btn_size, fb_y-btn_size, fb_x-offset+btn_size, fb_y+btn_size, fill=BTN_NORMAL, outline=ACCENT, width=2)
    canvas.create_text(fb_x-offset, fb_y, text="X", fill=TEXT, font=("Arial", 8, "bold"))

    # B Button (Right)
    controller_shapes["B"] = canvas.create_oval(fb_x+offset-btn_size, fb_y-btn_size, fb_x+offset+btn_size, fb_y+btn_size, fill=BTN_NORMAL, outline=ACCENT, width=2)
    canvas.create_text(fb_x+offset, fb_y, text="B", fill=TEXT, font=("Arial", 8, "bold"))


def create_gui():
    root = tk.Tk()
    root.title("TurboOne")
    root.geometry("850x500")
    root.configure(bg=BG_COLOR)
    root.resizable(False, False)

    # --- Header Branding ---
    header = tk.Label(root, text="TurboOne", bg=BG_COLOR, fg=BTN_GLOW, font=("Arial", 24, "bold", "italic"))
    header.pack(pady=(15, 5), anchor="w", padx=30)
    
    main_frame = tk.Frame(root, bg=BG_COLOR)
    main_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # --- Left Side: Button Matrix Calibrator Canvas ---
    canvas_frame = tk.Frame(main_frame, bg=BG_COLOR)
    canvas_frame.pack(side="left", fill="both", expand=True)
    
    tk.Label(canvas_frame, text="Input Calibrator (Matrix Layout)", bg=BG_COLOR, fg="#888888", font=("Arial", 12)).pack(anchor="n")
    
    c = tk.Canvas(canvas_frame, width=400, height=360, bg=BG_COLOR, highlightthickness=0)
    c.pack(pady=10)
    draw_controller(c)

    # --- Right Side: Turbo Configuration Panel ---
    control_frame = tk.Frame(main_frame, bg=PANEL_COLOR, bd=0)
    control_frame.pack(side="right", fill="y", ipadx=10, ipady=10)
    
    tk.Label(control_frame, text="Turbo Settings", bg=PANEL_COLOR, fg="white", font=("Arial", 12, "bold")).pack(pady=(15, 15))

    # Split controls into two columns for a clean software look
    grid_frame = tk.Frame(control_frame, bg=PANEL_COLOR)
    grid_frame.pack(padx=20)

    col1_btns = ["LT", "LB", "LS", "UP", "DOWN", "LEFT", "RIGHT", "BACK"]
    col2_btns = ["RT", "RB", "RS", "Y", "X", "A", "B", "START"]

    for col_idx, btn_list in enumerate([col1_btns, col2_btns]):
        for row_idx, btn_name in enumerate(btn_list):
            
            row_frame = tk.Frame(grid_frame, bg=PANEL_COLOR)
            row_frame.grid(row=row_idx, column=col_idx, padx=15, pady=6, sticky="w")
            
            # Button Label
            tk.Label(row_frame, text=btn_name, bg=PANEL_COLOR, fg="#cccccc", font=("Arial", 10, "bold"), width=5, anchor="w").pack(side="left")
            
            # Delay Input Box
            delay_var = tk.StringVar(value="25")
            entry = tk.Entry(row_frame, textvariable=delay_var, width=4, justify="center", bg="#2a2a2a", fg="white", bd=0, insertbackground="white")
            entry.pack(side="left", padx=(0, 2))
            
            tk.Label(row_frame, text="ms", bg=PANEL_COLOR, fg="#666666", font=("Arial", 8)).pack(side="left", padx=(0, 10))
            
            # Sleek Toggle Button
            toggle_btn = tk.Button(row_frame, text="OFF", width=6, bg=TURBO_OFF_BG, fg="#aaaaaa", font=("Arial", 9, "bold"), relief="flat", activebackground="#555555", cursor="hand2")
            toggle_btn.pack(side="left")
            
            # Bind the command
            toggle_btn.config(command=lambda n=btn_name, w=toggle_btn, v=delay_var, e=entry: toggle_macro(n, w, v, e))

    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))
    
    # Start the polling loop for the canvas lights
    poll_controller_state(root, c)
    
    return root

if __name__ == "__main__":
    gamepad_thread = threading.Thread(target=gamepad_loop, daemon=True)
    gamepad_thread.start()

    app = create_gui()
    app.mainloop()