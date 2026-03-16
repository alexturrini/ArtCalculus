import tkinter as tk
from tkinter import messagebox

BOX_SIZE = 20
STEPS = 32

current_channel = "r"

def get_fixed_values():
    try:
        r = int(r_entry.get())
        g = int(g_entry.get())
        b = int(b_entry.get())

        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            raise ValueError

        return r, g, b
    except:
        messagebox.showerror("Invalid Input", "RGB values must be 0–255")
        return None

def draw_gradient():
    vals = get_fixed_values()
    if not vals:
        return

    r, g, b = vals
    canvas.delete("all")

    for i in range(STEPS):
        value = int(i * 255 / (STEPS-1))

        rr, gg, bb = r, g, b

        if current_channel == "r":
            rr = value
        elif current_channel == "g":
            gg = value
        elif current_channel == "b":
            bb = value

        hex_color = f"#{rr:02x}{gg:02x}{bb:02x}"

        x0 = i * BOX_SIZE
        x1 = x0 + BOX_SIZE

        canvas.create_rectangle(
            x0, 0, x1, BOX_SIZE,
            fill=hex_color,
            outline=""
        )

def set_channel(channel):
    global current_channel
    current_channel = channel
    draw_gradient()

root = tk.Tk()
root.title("RGB Gradient Explorer")
root.geometry("450x220")

# RGB input fields
input_frame = tk.Frame(root)
input_frame.pack(pady=10)

tk.Label(input_frame, text="R").grid(row=0, column=0)
r_entry = tk.Entry(input_frame, width=5)
r_entry.insert(0,"128")
r_entry.grid(row=0, column=1)

tk.Label(input_frame, text="G").grid(row=0, column=2)
g_entry = tk.Entry(input_frame, width=5)
g_entry.insert(0,"128")
g_entry.grid(row=0, column=3)

tk.Label(input_frame, text="B").grid(row=0, column=4)
b_entry = tk.Entry(input_frame, width=5)
b_entry.insert(0,"128")
b_entry.grid(row=0, column=5)

update_btn = tk.Button(root, text="Update Gradient", command=draw_gradient)
update_btn.pack()

# Channel selection buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

tk.Button(button_frame, text="Vary Red", command=lambda: set_channel("r")).grid(row=0,column=0,padx=5)
tk.Button(button_frame, text="Vary Green", command=lambda: set_channel("g")).grid(row=0,column=1,padx=5)
tk.Button(button_frame, text="Vary Blue", command=lambda: set_channel("b")).grid(row=0,column=2,padx=5)

# Gradient display
canvas = tk.Canvas(root, width=BOX_SIZE*STEPS, height=BOX_SIZE)
canvas.pack(pady=10)

draw_gradient()

root.mainloop()