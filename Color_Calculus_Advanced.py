import tkinter as tk
from tkinter import messagebox

SIZE = 256
MARGIN = 60
FIXED_CHANNEL = "b"

def rgb_to_hex(r,g,b):
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

def get_fixed_value():
    try:
        v = float(fixed_entry.get())
        if not (0 <= v <= 1):
            raise ValueError
        return v
    except:
        messagebox.showerror("Invalid Input","Value must be between 0 and 1")
        return None

def axis_names():
    if FIXED_CHANNEL == "r":
        return "Green","Blue"
    if FIXED_CHANNEL == "g":
        return "Red","Blue"
    return "Red","Green"

def corner_values(fixed):

    if FIXED_CHANNEL == "r":
        return (
            (fixed,0,0),
            (fixed,1,0),
            (fixed,0,1),
            (fixed,1,1)
        )

    if FIXED_CHANNEL == "g":
        return (
            (0,fixed,0),
            (1,fixed,0),
            (0,fixed,1),
            (1,fixed,1)
        )

    return (
        (0,0,fixed),
        (1,0,fixed),
        (0,1,fixed),
        (1,1,fixed)
    )

def draw_gradient():

    fixed = get_fixed_value()
    if fixed is None:
        return

    canvas.delete("all")

    xname,yname = axis_names()

    for x in range(SIZE):
        for y in range(SIZE):

            r=g=b=0

            if FIXED_CHANNEL=="r":
                r=fixed
                g=x/(SIZE-1)
                b=1-y/(SIZE-1)

            elif FIXED_CHANNEL=="g":
                g=fixed
                r=x/(SIZE-1)
                b=1-y/(SIZE-1)

            else:
                b=fixed
                r=x/(SIZE-1)
                g=1-y/(SIZE-1)

            color=rgb_to_hex(r,g,b)

            canvas.create_line(
                MARGIN+x,
                MARGIN+y,
                MARGIN+x+1,
                MARGIN+y,
                fill=color
            )

    draw_axes(xname,yname,fixed)

def draw_axes(xname,yname,fixed):

    left=MARGIN
    top=MARGIN
    right=MARGIN+SIZE
    bottom=MARGIN+SIZE

    canvas.create_line(left,bottom,right,bottom,width=2)
    canvas.create_line(left,top,left,bottom,width=2)

    canvas.create_text((left+right)/2,bottom+35,text=xname)
    canvas.create_text(left-45,(top+bottom)/2,text=yname,angle=90)

    bl,br,tl,tr = corner_values(fixed)

    def fmt(c):
        return f"({c[0]:.1f},{c[1]:.1f},{c[2]:.1f})"

    canvas.create_text(left,bottom+15,text=fmt(bl),anchor="nw")
    canvas.create_text(right,bottom+15,text=fmt(br),anchor="ne")
    canvas.create_text(left-10,top,text=fmt(tl),anchor="ne")
    canvas.create_text(right,top,text=fmt(tr),anchor="nw")

def gradient_click(event):

    x=event.x-MARGIN
    y=event.y-MARGIN

    if not (0<=x<SIZE and 0<=y<SIZE):
        return

    fixed=get_fixed_value()
    if fixed is None:
        return

    xf=x/(SIZE-1)
    yf=y/(SIZE-1)

    if FIXED_CHANNEL=="r":
        r=fixed
        g=xf
        b=1-yf

    elif FIXED_CHANNEL=="g":
        g=fixed
        r=xf
        b=1-yf

    else:
        b=fixed
        r=xf
        g=1-yf

    hex_color=rgb_to_hex(r,g,b)

    rgb_label.config(
        text=f"R={r:.3f}  G={g:.3f}  B={b:.3f}    {hex_color.upper()}"
    )

def set_fixed(channel):
    global FIXED_CHANNEL
    FIXED_CHANNEL=channel
    draw_gradient()

root=tk.Tk()
root.title("2D RGB Color Space Explorer")
root.geometry("460x500")

rgb_label=tk.Label(root,text="Click inside plot to read color")
rgb_label.pack(pady=10)

input_frame=tk.Frame(root)
input_frame.pack(pady=10)

tk.Label(input_frame,text="Fixed value (0–1):").grid(row=0,column=0)

fixed_entry=tk.Entry(input_frame,width=6)
fixed_entry.insert(0,"0.5")
fixed_entry.grid(row=0,column=1)

tk.Button(
    input_frame,
    text="Update Gradient",
    command=draw_gradient
).grid(row=0,column=2,padx=5)

btn_frame=tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame,text="Fix Red",
          command=lambda:set_fixed("r")).grid(row=0,column=0,padx=5)

tk.Button(btn_frame,text="Fix Green",
          command=lambda:set_fixed("g")).grid(row=0,column=1,padx=5)

tk.Button(btn_frame,text="Fix Blue",
          command=lambda:set_fixed("b")).grid(row=0,column=2,padx=5)

canvas=tk.Canvas(root,width=SIZE+MARGIN*2,height=SIZE+MARGIN*2)
canvas.pack()

canvas.bind("<Button-1>",gradient_click)

draw_gradient()

root.mainloop()