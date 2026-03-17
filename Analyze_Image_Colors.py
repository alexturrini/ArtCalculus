import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
from PIL import Image, ImageTk
from sklearn.cluster import MiniBatchKMeans
import numpy as np
import csv
import os

class ClusteredColorEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Clustered RGB Color Editor")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(4, weight=1)

        # ---------------- Variables ----------------
        self.original_img = None
        self.display_img = None
        self.pixel_array = None
        self.original_pixel_array = None
        self.cluster_labels = None
        self.cluster_centroids = None
        self.n_clusters = 10
        self.thumbnail_size = (300, 300)
        self.image_name_for_csv = "colors.csv"

        # Track colors manually updated by user
        self.user_updated_colors = {}

        # ---------------- GUI Setup ----------------
        self.setup_input_frame()
        self.setup_buttons_frame()
        self.setup_image_frame()
        self.setup_colors_frame()
        self.setup_status_frame()

    # ---------------- GUI Frames ----------------
    def setup_input_frame(self):
        frame = tk.Frame(self.root, bg="#f0f0f0", pady=5)
        frame.grid(row=0, column=0, sticky="ew", padx=10)
        frame.columnconfigure(1, weight=1)

        tk.Label(frame, text="Image File:", bg="#f0f0f0").grid(row=0, column=0, sticky="e")
        self.image_entry = tk.Entry(frame)
        self.image_entry.grid(row=0, column=1, sticky="ew", padx=5)
        tk.Button(frame, text="Browse...", command=self.select_image).grid(row=0, column=2)

        tk.Label(frame, text="Output CSV File Name:", bg="#f0f0f0").grid(row=1, column=0, sticky="e")
        self.output_entry = tk.Entry(frame)
        self.output_entry.grid(row=1, column=1, sticky="ew", padx=5)
        self.output_entry.insert(0, self.image_name_for_csv)

        tk.Label(frame, text="Number of Clusters:", bg="#f0f0f0").grid(row=2, column=0, sticky="e")
        self.cluster_entry = tk.Entry(frame, width=10)
        self.cluster_entry.grid(row=2, column=1, sticky="w", padx=5)
        self.cluster_entry.insert(0, "10")

    def setup_buttons_frame(self):
        frame = tk.Frame(self.root, bg="#f0f0f0", pady=5)
        frame.grid(row=1, column=0, sticky="ew", padx=10)
        frame.columnconfigure((0,1,2), weight=1)

        ttk.Button(frame, text="Run KMeans Clustering", command=self.run_processing).grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Button(frame, text="Save Image", command=self.save_image).grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(frame, text="Reset Image", command=self.reset_image).grid(row=0, column=2, padx=5, sticky="ew")

    def setup_image_frame(self):
        frame = tk.Frame(self.root, bg="#d0d0d0", bd=2, relief="sunken")
        frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.image_label = tk.Label(frame)
        self.image_label.grid(sticky="nsew")

    def setup_colors_frame(self):
        label = tk.Label(self.root, text="Top Clustered Colors:", bg="#f0f0f0")
        label.grid(row=3, column=0, sticky="w", padx=10)

        container = tk.Frame(self.root)
        container.grid(row=4, column=0, sticky="nsew", padx=10)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        canvas = tk.Canvas(container, height=150)
        canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(container, orient="horizontal", command=canvas.xview)
        scrollbar.grid(row=1, column=0, sticky="ew")
        canvas.configure(xscrollcommand=scrollbar.set)

        self.colors_frame = tk.Frame(canvas)
        canvas.create_window((0,0), window=self.colors_frame, anchor="nw")
        self.colors_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    def setup_status_frame(self):
        frame = tk.Frame(self.root, bg="#f0f0f0")
        frame.grid(row=5, column=0, sticky="ew", padx=10, pady=5)
        frame.columnconfigure(1, weight=1)

        tk.Label(frame, text="Status:", bg="#f0f0f0").grid(row=0, column=0, sticky="w")
        self.status_label = tk.Label(frame, text="Idle", bg="#f0f0f0")
        self.status_label.grid(row=0, column=1, sticky="w")

        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.grid(row=0, column=2, sticky="e")

    # ---------------- Image Handling ----------------
    def select_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files","*.png *.jpg *.jpeg *.bmp *.gif")])
        if file_path:
            self.image_entry.delete(0, tk.END)
            self.image_entry.insert(0, file_path)
            self.original_img = Image.open(file_path).convert("RGB")
            self.original_pixel_array = np.array(self.original_img.getdata())
            self.pixel_array = self.original_pixel_array.copy()
            self.display_image(self.original_img)

            base_name = os.path.basename(file_path)
            name_without_ext = os.path.splitext(base_name)[0]
            cluster_count = self.cluster_entry.get()
            self.image_name_for_csv = f"KMeans_{cluster_count}_Clusters_{name_without_ext}.csv"
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, self.image_name_for_csv)

            # Reset clusters and user edits
            self.cluster_labels = None
            self.cluster_centroids = None
            self.user_updated_colors = {}

    def display_image(self, img):
        self.display_img = img.copy()
        self.display_img.thumbnail((300, 300))
        img_tk = ImageTk.PhotoImage(self.display_img)
        self.image_label.configure(image=img_tk)
        self.image_label.image = img_tk

    # ---------------- Color Processing ----------------
    def count_colors(self, image, n_clusters):
        pixel_data = np.array(image.getdata())
        total_pixels = pixel_data.shape[0]
        sample_size = min(5000, total_pixels)
        sampled_pixels = pixel_data[np.random.choice(total_pixels, sample_size, replace=False)] if total_pixels > sample_size else pixel_data

        kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, batch_size=1000)
        kmeans.fit(sampled_pixels)
        centroids = np.round(kmeans.cluster_centers_).astype(int)
        self.cluster_centroids = centroids

        labels = np.argmin(np.linalg.norm(pixel_data[:, None, :] - centroids[None, :, :], axis=2), axis=1)
        self.cluster_labels = labels
        self.pixel_array = pixel_data.copy()

        unique, counts = np.unique(labels, return_counts=True)
        sorted_colors = sorted(
            [(tuple(centroids[i]), counts[idx], i) for idx, i in enumerate(unique)],
            key=lambda x: x[1], reverse=True
        )
        return sorted_colors

    # ---------------- GUI Interaction ----------------
    def show_top_colors(self):
        if self.cluster_centroids is None or self.cluster_labels is None:
            return

        # Build sorted color list, using user-edited colors
        colors = [
            (self.user_updated_colors.get(i, tuple(self.cluster_centroids[i])),
             np.sum(self.cluster_labels == i),
             i)
            for i in range(self.n_clusters)
        ]
        sorted_colors = sorted(colors, key=lambda x: x[1], reverse=True)

        for widget in self.colors_frame.winfo_children():
            widget.destroy()
        for i, (color_tuple, count, cluster_index) in enumerate(sorted_colors):
            r, g, b = color_tuple
            color_hex = f"#{r:02x}{g:02x}{b:02x}"
            frame = tk.Frame(self.colors_frame, padx=5, pady=5)
            frame.grid(row=0, column=i)
            swatch = tk.Label(frame, bg=color_hex, width=6, height=3, relief="raised", bd=1)
            swatch.pack()
            swatch.bind("<Button-1>", lambda e, idx=cluster_index: self.replace_cluster_color(idx))
            tk.Label(frame, text=f"{r},{g},{b}\n{count}", font=("Arial", 8)).pack()

    def replace_cluster_color(self, cluster_index):
        if self.cluster_centroids is None or self.cluster_labels is None:
            return

        current_color = self.user_updated_colors.get(cluster_index, tuple(self.cluster_centroids[cluster_index]))
        new_color = colorchooser.askcolor(color=current_color, title=f"Select new color for cluster {cluster_index}")
        if new_color[0] is not None:
            rgb = tuple(map(int, new_color[0]))
            # Update pixel array
            self.pixel_array[self.cluster_labels == cluster_index] = rgb
            self.user_updated_colors[cluster_index] = rgb

            updated_img = Image.new("RGB", self.original_img.size)
            updated_img.putdata([tuple(p) for p in self.pixel_array])
            self.original_img = updated_img
            self.display_image(self.original_img)

            # Update swatches, preserving user-edited colors
            self.show_top_colors()

    def reset_image(self):
        if self.original_pixel_array is not None:
            self.pixel_array = self.original_pixel_array.copy()
            self.original_img.putdata([tuple(p) for p in self.pixel_array])
            self.display_image(self.original_img)
            # Clear user edits
            self.user_updated_colors = {}
            self.show_top_colors()

    # ---------------- CSV & Save ----------------
    def save_csv(self, filename):
        colors = [
            (self.user_updated_colors.get(i, tuple(self.cluster_centroids[i])), np.sum(self.cluster_labels == i), i)
            for i in range(self.n_clusters)
        ]
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["R","G","B","Count"])
            for color, count, _ in colors:
                writer.writerow([*color, count])

    def save_image(self):
        if self.original_img is None:
            messagebox.showerror("Error", "No image to save.")
            return

        if self.image_entry.get():
            base_name = os.path.basename(self.image_entry.get())
            name_without_ext = os.path.splitext(base_name)[0]
            default_name = f"{name_without_ext}_"
        else:
            default_name = "Image_"

        file_path = filedialog.asksaveasfilename(
            initialfile=default_name,
            defaultextension=".png",
            filetypes=[("PNG files","*.png"),("JPEG files","*.jpg"),("All files","*.*")]
        )
        if file_path:
            self.original_img.save(file_path)
            messagebox.showinfo("Saved", f"Image saved to {file_path}")

    # ---------------- Processing ----------------
    def run_processing(self):
        if self.original_img is None:
            messagebox.showerror("Error", "Select an image first.")
            return
        try:
            self.n_clusters = int(self.cluster_entry.get())
            if self.n_clusters < 1:
                self.n_clusters = 10
        except:
            self.n_clusters = 10

        output_file = self.output_entry.get().strip()
        if not output_file.lower().endswith(".csv"):
            output_file += ".csv"

        self.status_label.config(text="Processing...")
        self.progress.start()
        self.root.update_idletasks()

        try:
            self.count_colors(self.original_img, self.n_clusters)
            self.show_top_colors()
            save_path = os.path.join(os.path.dirname(self.image_entry.get()), output_file)
            self.save_csv(save_path)
            self.status_label.config(text=f"Done! CSV saved to {save_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_label.config(text="Error occurred")
        finally:
            self.progress.stop()


if __name__ == "__main__":
    root = tk.Tk()
    app = ClusteredColorEditor(root)
    root.mainloop()