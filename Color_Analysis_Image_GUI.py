import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from collections import Counter
import csv
import os

# Global variables to keep track of the current image
original_img = None   # full-resolution image
display_img = None    # resized for GUI display

def quantize_color(pixel, bin_size):
    r, g, b = pixel
    return (
        (r // bin_size) * bin_size,
        (g // bin_size) * bin_size,
        (b // bin_size) * bin_size
    )

def count_colors(image, bin_size=1):
    pixels = list(image.getdata())
    if bin_size > 1:
        pixels = [quantize_color(p, bin_size) for p in pixels]
    color_counts = Counter(pixels)
    return color_counts.most_common()

def save_csv(sorted_colors, output_file):
    with open(output_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["R", "G", "B", "Count"])
        for (r, g, b), count in sorted_colors:
            writer.writerow([r, g, b, count])

# --- GUI functions ---
def select_image():
    global original_img, display_img
    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif")]
    )
    if file_path:
        image_entry.delete(0, tk.END)
        image_entry.insert(0, file_path)
        original_img = Image.open(file_path).convert("RGB")
        display_image(original_img)

def display_image(img):
    global display_img
    # Resize for display
    display_img = img.copy()
    display_img.thumbnail((300, 300))
    img_tk = ImageTk.PhotoImage(display_img)
    image_label.config(image=img_tk)
    image_label.image = img_tk  # keep reference

def show_top_colors(sorted_colors):
    # Clear previous colors
    for widget in colors_frame.winfo_children():
        widget.destroy()

    num_colors = min(10, len(sorted_colors))
    top_colors = sorted_colors[:num_colors]

    rows = (num_colors + 4) // 5  # max 2 rows

    for i, ((r, g, b), count) in enumerate(top_colors):
        row = i // 5
        col_in_row = i % 5
        colors_in_this_row = min(5, num_colors - row*5)
        empty_columns = (5 - colors_in_this_row) // 2
        col = col_in_row + empty_columns

        color_hex = f"#{r:02x}{g:02x}{b:02x}"

        frame = tk.Frame(colors_frame, padx=5, pady=5)
        frame.grid(row=row, column=col)

        # Make swatch clickable
        swatch = tk.Label(frame, bg=color_hex, width=6, height=3)
        swatch.pack()
        swatch.bind("<Button-1>", lambda e, color=(r,g,b): replace_color_popup(color))

        label = tk.Label(frame, text=f"{r},{g},{b}\n{count}")
        label.pack()

def replace_color_popup(color_to_replace):
    popup = tk.Toplevel(root)
    popup.title(f"Replace color {color_to_replace}")

    tk.Label(popup, text="New R:").grid(row=0, column=0)
    r_entry = tk.Entry(popup, width=5)
    r_entry.grid(row=0, column=1)
    tk.Label(popup, text="G:").grid(row=1, column=0)
    g_entry = tk.Entry(popup, width=5)
    g_entry.grid(row=1, column=1)
    tk.Label(popup, text="B:").grid(row=2, column=0)
    b_entry = tk.Entry(popup, width=5)
    b_entry.grid(row=2, column=1)

    def apply_replacement():
        try:
            new_r = int(r_entry.get())
            new_g = int(g_entry.get())
            new_b = int(b_entry.get())
            for v in (new_r, new_g, new_b):
                if v < 0 or v > 255:
                    raise ValueError
        except:
            messagebox.showerror("Error", "RGB values must be integers 0-255")
            return

        replace_color_in_image(color_to_replace, (new_r, new_g, new_b))
        popup.destroy()

    tk.Button(popup, text="Apply", command=apply_replacement).grid(row=3, column=0, columnspan=2, pady=5)

def replace_color_in_image(old_color, new_color):
    global original_img, display_img
    if original_img is None:
        return

    pixels = list(original_img.getdata())
    pixels = [new_color if p==old_color else p for p in pixels]
    original_img.putdata(pixels)
    display_image(original_img)

    # Update top colors after replacement
    try:
        bin_size = int(bin_entry.get())
        if bin_size < 1 or bin_size > 256:
            bin_size = 1
    except:
        bin_size = 1

    sorted_colors = count_colors(original_img, bin_size)
    show_top_colors(sorted_colors)

def run_processing():
    filename = output_entry.get().strip()
    try:
        bin_size = int(bin_entry.get())
        if bin_size < 1 or bin_size > 256:
            bin_size = 1
    except:
        bin_size = 1

    if original_img is None:
        messagebox.showerror("Error", "Please select an image first.")
        return
    if not filename:
        messagebox.showerror("Error", "Please enter an output file name.")
        return
    if not filename.lower().endswith(".csv"):
        filename += ".csv"

    output_path = os.path.join(os.path.dirname(image_entry.get()), filename)

    try:
        status_label.config(text="Processing...")
        root.update()

        sorted_colors = count_colors(original_img, bin_size)
        save_csv(sorted_colors, output_path)
        show_top_colors(sorted_colors)

        status_label.config(text="Done!")
        messagebox.showinfo("Success", f"Saved to:\n{output_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))
        status_label.config(text="Error occurred")

def save_image():
    global original_img
    if original_img is None:
        messagebox.showerror("Error", "No image to save.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".jpg",
        filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png"), ("All files", "*.*")]
    )
    if file_path:
        try:
            original_img.save(file_path)
            messagebox.showinfo("Success", f"Image saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

# --- GUI Setup ---
root = tk.Tk()
root.title("RGB Color Counter and Editor")

# Image selection
tk.Label(root, text="Image File:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
image_entry = tk.Entry(root, width=40)
image_entry.grid(row=0, column=1, padx=5, pady=5)
tk.Button(root, text="Browse...", command=select_image).grid(row=0, column=2, padx=5)

# Output filename for CSV
tk.Label(root, text="Output File Name:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
output_entry = tk.Entry(root, width=40)
output_entry.grid(row=1, column=1, padx=5, pady=5)
output_entry.insert(0, "colors.csv")

# Bin size
tk.Label(root, text="Bin Size (1-256):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
bin_entry = tk.Entry(root, width=10)
bin_entry.grid(row=2, column=1, sticky="w", padx=5)
bin_entry.insert(0, "1")  # default no quantization

# Run CSV button
tk.Button(root, text="Run CSV", command=run_processing, width=20).grid(
    row=3, column=0, columnspan=3, pady=5
)

# Save Image button
tk.Button(root, text="Save Image", command=save_image, width=20).grid(
    row=4, column=0, columnspan=3, pady=5
)

# Image display
image_label = tk.Label(root)
image_label.grid(row=5, column=0, columnspan=3, pady=10)

# Top colors label
tk.Label(root, text="Top 10 Colors:").grid(row=6, column=0, columnspan=3)

# Frame for colors
colors_frame = tk.Frame(root)
colors_frame.grid(row=7, column=0, columnspan=3, pady=5)

# Status
status_label = tk.Label(root, text="Idle")
status_label.grid(row=8, column=0, columnspan=3, pady=5)

root.mainloop()