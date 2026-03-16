import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, RadioButtons

SIZE = 256
fixed_channel = "Blue"
fixed_value = 0.5

fig, ax = plt.subplots()
plt.subplots_adjust(left=0.3, bottom=0.25)

# placeholder image
img = ax.imshow(np.zeros((SIZE,SIZE,3)))

def generate_slice():

    global fixed_value

    x = np.linspace(0,1,SIZE)
    y = np.linspace(0,1,SIZE)

    X,Y = np.meshgrid(x,y)

    rgb = np.zeros((SIZE,SIZE,3))

    if fixed_channel == "Red":
        rgb[:,:,0] = fixed_value
        rgb[:,:,1] = X
        rgb[:,:,2] = 1-Y
        xlabel="Green"
        ylabel="Blue"

    elif fixed_channel == "Green":
        rgb[:,:,1] = fixed_value
        rgb[:,:,0] = X
        rgb[:,:,2] = 1-Y
        xlabel="Red"
        ylabel="Blue"

    else:
        rgb[:,:,2] = fixed_value
        rgb[:,:,0] = X
        rgb[:,:,1] = 1-Y
        xlabel="Red"
        ylabel="Green"

    ax.clear()

    ax.imshow(rgb, origin="lower", extent=[0,1,0,1])

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    ax.set_xticks([0,0.25,0.5,0.75,1])
    ax.set_yticks([0,0.25,0.5,0.75,1])

    ax.set_title(f"{fixed_channel} fixed at {fixed_value:.2f}")

    fig.canvas.draw_idle()

generate_slice()

# fixed value input
axbox = plt.axes([0.3,0.1,0.4,0.05])
textbox = TextBox(axbox,"Fixed value (0-1): ",initial=str(fixed_value))

def submit(text):
    global fixed_value
    try:
        v=float(text)
        if 0<=v<=1:
            fixed_value=v
            generate_slice()
    except:
        pass

textbox.on_submit(submit)

# channel selector
rax = plt.axes([0.05,0.4,0.2,0.2])
radio = RadioButtons(rax,("Red","Green","Blue"))

def change_channel(label):
    global fixed_channel
    fixed_channel=label
    generate_slice()

radio.on_clicked(change_channel)

# click readout
def onclick(event):

    if event.inaxes!=ax:
        return

    x=event.xdata
    y=event.ydata

    if fixed_channel=="Red":
        r=fixed_value
        g=x
        b=1-y

    elif fixed_channel=="Green":
        g=fixed_value
        r=x
        b=1-y

    else:
        b=fixed_value
        r=x
        g=1-y

    r,g,b=[max(0,min(1,v)) for v in (r,g,b)]

    hex_color=f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    print(f"R={r:.3f}  G={g:.3f}  B={b:.3f}   {hex_color}")

fig.canvas.mpl_connect("button_press_event",onclick)

plt.show()