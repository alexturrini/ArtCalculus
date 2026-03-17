import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from collections import Counter
from sklearn.cluster import KMeans
import numpy as np
import csv
import os

# ------------------- Global Variables -------------------
original_img = None      # Full image
display_img = None       # Resized preview
cluster_labels = None    # Cluster assignment for each pixel
pixel_array = None       # Flattened pixel array

# ------------------- Color Counting Functions -------------------
def count_colors(image, n_clusters=10):
    """Count top colors using K-Means clustering and return cluster info."""
    global cluster_labels, pixel_array
    pixels = np.array(image.getdata())
    pixel_array = pixels.copy()
    n_clusters = min(n_clusters, len(pixels))
    if n_clusters == 0:
        return [], None

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(pixels)
    cluster_labels = labels
    centroids = np.round(kmeans.cluster_centers_).astype(int)

    label_counts = Counter(labels)
    sorted_colors = sorted(
        [(tuple(centroids[label]), count, label) for label, count in label_counts.items()],
        key=lambda x: x[1],
        reverse=True
    )
    return sorted_colors, labels

def count_colors_unclustered(image):
    """Count exact RGB colors."""
    pixels = list(image.getdata())
    color_counts = Counter(pixels)
    return color_counts.most_common()

def save_csv_both(clustered_colors, unclustered_colors, output_file):
    """Save clustered and unclustered data to CSV."""
    with open(output_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        # Clustered data
        writer.writerow(["Clustered Colors (K-Means)"])
        writer.writerow(["R", "G", "B", "Count"])
        for color_tuple, count, cluster_index in clustered_colors:
            r, g, b = color_tuple
            writer.writerow([r, g, b, count])
        writer.writerow([])
        # Unclustered data
        writer.writerow(["Unclustered Colors (Exact)"])
        writer.writerow(["R", "G", "B", "Count"])
        for (r, g, b), count in unclustered_colors:
            writer.writerow([r, g, b, count])

# ------------------- GUI Functions -------------------
def select_image():
    global original_img
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
    display_img = img.copy()
    display_img.thumbnail((300, 300))
    img_tk = ImageTk.PhotoImage(display_img)
    image_label.config(image=img_tk)
    image_label.image = img_tk

def show_top_colors(sorted_colors):
    """Display top 10 clustered colors in a 2-row grid."""
    for widget in colors_frame.winfo_children():
        widget.destroy()

    num_colors = min(10, len(sorted_colors))
    top_colors = sorted_colors[:num_colors]

    for i, (color_tuple, count, cluster_index) in enumerate(top_colors):
        r, g, b = color_tuple
        row = i // 5
        col_in_row = i % 5
        colors_in_this_row = min(5, num_colors - row*5)
        empty_columns = (5 - colors_in_this_row) // 2
        col = col_in_row + empty_columns

        color_hex = f"#{r:02x}{g:02x}{b:02x}"
        frame = tk.Frame(colors_frame, padx=5, pady=5)
        frame.grid(row=row, column=col)

        swatch = tk.Label(frame, bg=color_hex, width=6, height=3)
        swatch.pack()
        swatch.bind("<Button-1>", lambda e, c_idx=cluster_index: replace_cluster_popup(c_idx))

        label = tk.Label(frame, text=f"{r},{g},{b}\n{count}")
        label.pack()

def replace_cluster_popup(cluster_index):
    """Popup to replace all pixels in the selected cluster."""
    popup = tk.Toplevel(root)
    popup.title(f"Replace all pixels in cluster {cluster_index}")

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

        replace_cluster_in_image(cluster_index, (new_r, new_g, new_b))
        popup.destroy()

    tk.Button(popup, text="Apply", command=apply_replacement).grid(
        row=3, column=0, columnspan=2, pady=5
    )

def replace_cluster_in_image(cluster_index, new_color):
    """Replace all pixels assigned to a specific cluster."""
    global original_img, cluster_labels, pixel_array
    if original_img is None or cluster_labels is None or pixel_array is None:
        return

    new_pixels = [
        tuple(new_color) if cluster_labels[i] == cluster_index else tuple(pixel_array[i])
        for i in range(len(pixel_array))
    ]
    original_img.putdata(new_pixels)
    display_image(original_img)
    run_processing(update_display_only=True)

def run_processing(update_display_only=False):
    """Run clustering, update GUI, and optionally save CSV."""
    global cluster_labels, pixel_array
    filename = output_entry.get().strip()
    try:
        n_clusters = int(bin_entry.get())
        if n_clusters < 1:
            n_clusters = 10
    except:
        n_clusters = 10

    if original_img is None:
        messagebox.showerror("Error", "Please select an image first.")
        return
    if not update_display_only and not filename:
        messagebox.showerror("Error", "Please enter an output file name.")
        return
    if not update_display_only and not filename.lower().endswith(".csv"):
        filename += ".csv"

    try:
        status_label.config(text="Processing...")
        root.update()

        # Clustered colors
        clustered_colors, _ = count_colors(original_img, n_clusters)
        show_top_colors(clustered_colors)

        # Unclustered colors
        unclustered_colors = count_colors_unclustered(original_img)

        if not update_display_only:
            output_path = os.path.join(os.path.dirname(image_entry.get()), filename)
            save_csv_both(clustered_colors, unclustered_colors, output_path)
            messagebox.showinfo("Success", f"Saved to:\n{output_path}")

        status_label.config(text="Done!")
    except Exception as e:
        messagebox.showerror("Error", str(e))
        status_label.config(text="Error occurred")

def save_image():
    if original_img is None:
        messagebox.showerror("Error", "No image to save.")
        return
    file_path = filedialog.asksaveasfilename(
        defaultextension=".jpg",
        filetypes=[("JPEG files","*.jpg"),("PNG files","*.png"),("All files","*.*")]
    )
    if file_path:
        try:
            original_img.save(file_path)
            messagebox.showinfo("Success", f"Image saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

# ------------------- GUI Setup -------------------
root = tk.Tk()
root.title("Clustered RGB Color Editor")

# Image selection
tk.Label(root, text="Image File:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
image_entry = tk.Entry(root, width=40)
image_entry.grid(row=0, column=1, padx=5, pady=5)
tk.Button(root, text="Browse...", command=select_image).grid(row=0, column=2, padx=5)

# CSV output filename
tk.Label(root, text="Output CSV File Name:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
output_entry = tk.Entry(root, width=40)
output_entry.grid(row=1, column=1, padx=5, pady=5)
output_entry.insert(0, "colors.csv")

# Number of clusters
tk.Label(root, text="Number of Clusters (Top Colors):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
bin_entry = tk.Entry(root, width=10)
bin_entry.grid(row=2, column=1, sticky="w", padx=5)
bin_entry.insert(0, "10")

# Run CSV button
tk.Button(root, text="Run CSV", command=run_processing, width=20).grid(row=3, column=0, columnspan=3, pady=5)

# Save image button
tk.Button(root, text="Save Image", command=save_image, width=20).grid(row=4, column=0, columnspan=3, pady=5)

# Image display
image_label = tk.Label(root)
image_label.grid(row=5, column=0, columnspan=3, pady=10)

# Top colors label
tk.Label(root, text="Top 10 Clustered Colors:").grid(row=6, column=0, columnspan=3)

# Frame for colors
colors_frame = tk.Frame(root)
colors_frame.grid(row=7, column=0, columnspan=3, pady=5)

# Status label
status_label = tk.Label(root, text="Idle")
status_label.grid(row=8, column=0, columnspan=3, pady=5)

root.mainloop()