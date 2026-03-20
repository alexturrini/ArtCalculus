import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
from PIL import Image, ImageTk
from sklearn.cluster import MiniBatchKMeans
import numpy as np
import os
import csv
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pandas as pd
from scipy.spatial.distance import cdist
from scipy.stats import entropy
from collections import Counter

class ClusteredColorEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Clustered RGB Color Editor")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(5, weight=1)

        # Variables
        self.original_img = None
        self.display_img = None
        self.pixel_array = None
        self.original_pixel_array = None
        self.cluster_labels = None
        self.cluster_centroids = None
        self.original_cluster_centroids = None
        self.sampled_pixels_for_plot = None
        self.n_clusters = 10
        self.user_updated_colors = {}
        self.output_csv_name = "colors.csv"

        # GUI setup
        self.setup_input_frame()
        self.setup_buttons_frame()
        self.setup_image_frame()
        self.setup_colors_frame()
        self.setup_status_frame()

    # --- GUI frames ---
    def setup_input_frame(self):
        frame = tk.Frame(self.root, bg="#f0f0f0", pady=5)
        frame.grid(row=0, column=0, sticky="ew", padx=10)
        frame.columnconfigure(1, weight=1)

        # Image file
        tk.Label(frame, text="Image File:", bg="#f0f0f0").grid(row=0, column=0, sticky="e")
        self.image_entry = tk.Entry(frame)
        self.image_entry.grid(row=0, column=1, sticky="ew", padx=5)
        tk.Button(frame, text="Browse...", command=self.select_image).grid(row=0, column=2)

        # Output CSV file (above number of clusters)
        tk.Label(frame, text="Output CSV File:", bg="#f0f0f0").grid(row=1, column=0, sticky="e")
        self.csv_entry = tk.Entry(frame)
        self.csv_entry.grid(row=1, column=1, sticky="ew", padx=5)
        self.csv_entry.insert(0, self.output_csv_name)

        # Number of clusters
        tk.Label(frame, text="Number of Clusters:", bg="#f0f0f0").grid(row=2, column=0, sticky="e")
        self.cluster_entry = tk.Entry(frame, width=10)
        self.cluster_entry.grid(row=2, column=1, sticky="w", padx=5)
        self.cluster_entry.insert(0, "10")

    def setup_buttons_frame(self):
        frame = tk.Frame(self.root, bg="#f0f0f0", pady=5)
        frame.grid(row=1, column=0, sticky="ew", padx=10)
        frame.columnconfigure((0,1,2,3), weight=1)
        ttk.Button(frame, text="Run KMeans Clustering", command=self.run_processing).grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Button(frame, text="Save Image", command=self.save_image).grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(frame, text="Reset Image", command=self.reset_image).grid(row=0, column=2, padx=5, sticky="ew")
        ttk.Button(frame, text="Save CSV", command=self.save_csv_button).grid(row=0, column=3, padx=5, sticky="ew")

    def setup_image_frame(self):
        frame = tk.Frame(self.root, bg="#d0d0d0", bd=2, relief="sunken")
        frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)
        self.image_label = tk.Label(frame)
        self.image_label.grid(row=0, column=0, sticky="nsew")
        self.plot_frame = tk.Frame(frame, bg="white")
        self.plot_frame.grid(row=0, column=1, sticky="nsew")

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

    # --- Image Handling ---
    def select_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.image_entry.delete(0, tk.END)
            self.image_entry.insert(0, file_path)
            self.original_img = Image.open(file_path).convert("RGB")
            self.original_pixel_array = np.array(self.original_img.getdata())
            self.pixel_array = self.original_pixel_array.copy()
            self.display_image(self.original_img)
            # Initialize CSV filename from image name
            base_name = os.path.basename(file_path)
            name_no_ext = os.path.splitext(base_name)[0]
            default_csv = f"{name_no_ext}_clusters.csv"
            self.csv_entry.delete(0, tk.END)
            self.csv_entry.insert(0, default_csv)

    def display_image(self, img):
        self.display_img = img.copy()
        self.display_img.thumbnail((300, 300))
        img_tk = ImageTk.PhotoImage(self.display_img)
        self.image_label.configure(image=img_tk)
        self.image_label.image = img_tk

    # --- Clustering ---
    def count_colors(self, image, n_clusters):
        pixel_data = np.array(image.getdata())
        kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42)
        kmeans.fit(pixel_data)
        self.cluster_centroids = np.round(kmeans.cluster_centers_).astype(int)
        self.original_cluster_centroids = self.cluster_centroids.copy()
        sample_size = min(3000, len(pixel_data))
        idx = np.random.choice(len(pixel_data), sample_size, replace=False)
        self.sampled_pixels_for_plot = pixel_data[idx].copy()
        self.cluster_labels = kmeans.labels_
        self.pixel_array = pixel_data.copy()

    # --- CSV Export ---
    def save_csv(self, filename):
        """Save global image stats, cluster validation metrics, per-pixel data, and cluster-level statistics."""
        import pandas as pd
        import numpy as np
        from collections import Counter
        from scipy.spatial.distance import cdist
        from scipy.stats import entropy
        from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

        pixel_array = np.array(self.pixel_array)
        total_pixels = len(pixel_array)

        # Ensure centroids reflect user edits
        centroids = np.array([
            self.user_updated_colors.get(i, tuple(self.cluster_centroids[i]))
            for i in range(self.n_clusters)
        ], dtype=int)

        # --- Global image statistics ---
        mean_rgb = pixel_array.mean(axis=0).astype(int)
        std_rgb = pixel_array.std(axis=0).astype(float)

        # Color entropy per channel
        def channel_entropy(channel_values):
            counts = Counter(channel_values)
            probs = np.array(list(counts.values())) / len(channel_values)
            return entropy(probs, base=2)

        entropy_r = channel_entropy(pixel_array[:, 0])
        entropy_g = channel_entropy(pixel_array[:, 1])
        entropy_b = channel_entropy(pixel_array[:, 2])

        # Dominant cluster
        cluster_counts = Counter(self.cluster_labels)
        dominant_cluster = max(cluster_counts, key=cluster_counts.get)

        # --- Cluster validation metrics with pixel sampling ---
        sample_size = min(5000, total_pixels)
        sample_idx = np.random.choice(total_pixels, sample_size, replace=False)
        sample_pixels = pixel_array[sample_idx]
        sample_labels = self.cluster_labels[sample_idx]

        # Use existing inertia from KMeans
        inertia = getattr(self, "kmeans_inertia", None)
        if inertia is None:
            try:
                from sklearn.cluster import MiniBatchKMeans
                inertia = MiniBatchKMeans(n_clusters=self.n_clusters, random_state=42).fit(pixel_array).inertia_
            except:
                inertia = np.nan

        try:
            silhouette = silhouette_score(sample_pixels, sample_labels)
        except:
            silhouette = np.nan
        try:
            calinski_harabasz = calinski_harabasz_score(sample_pixels, sample_labels)
        except:
            calinski_harabasz = np.nan
        try:
            davies_bouldin = davies_bouldin_score(sample_pixels, sample_labels)
        except:
            davies_bouldin = np.nan

        # --- Per-pixel data ---
        distances = np.linalg.norm(pixel_array - centroids[self.cluster_labels], axis=1)
        pixel_df = pd.DataFrame({
            "Pixel_R": pixel_array[:, 0],
            "Pixel_G": pixel_array[:, 1],
            "Pixel_B": pixel_array[:, 2],
            "Cluster": self.cluster_labels,
            "Centroid_R": centroids[self.cluster_labels][:, 0],
            "Centroid_G": centroids[self.cluster_labels][:, 1],
            "Centroid_B": centroids[self.cluster_labels][:, 2],
            "Distance_to_Centroid": distances
        })

        # --- Cluster-level statistics ---
        cluster_stats = []
        for i in range(self.n_clusters):
            cluster_pixels = pixel_df[pixel_df["Cluster"] == i][["Pixel_R", "Pixel_G", "Pixel_B"]].values
            if len(cluster_pixels) == 0:
                continue
            mean_c = cluster_pixels.mean(axis=0)
            std_c = cluster_pixels.std(axis=0)
            min_c = cluster_pixels.min(axis=0)
            max_c = cluster_pixels.max(axis=0)
            mean_distance = np.mean(np.linalg.norm(cluster_pixels - centroids[i], axis=1))
            pixel_count = len(cluster_pixels)
            cluster_stats.append([
                i,
                pixel_count,
                pixel_count / total_pixels,
                *mean_c.astype(int),
                *std_c.astype(float),
                *min_c.astype(int),
                *max_c.astype(int),
                mean_distance
            ])
        cluster_df = pd.DataFrame(cluster_stats, columns=[
            "Cluster", "Pixel_Count", "Pixel_Proportion",
            "Mean_R", "Mean_G", "Mean_B",
            "Std_R", "Std_G", "Std_B",
            "Min_R", "Min_G", "Min_B",
            "Max_R", "Max_G", "Max_B",
            "Mean_Centroid_Distance"
        ])

        # --- Save all sections to CSV ---
        with open(filename, "w", newline="") as f:
            f.write("# Global Image Statistics\n")
            f.write(f"Total_Pixels,{total_pixels}\n")
            f.write(f"Mean_R,{mean_rgb[0]},Mean_G,{mean_rgb[1]},Mean_B,{mean_rgb[2]}\n")
            f.write(f"Std_R,{std_rgb[0]},Std_G,{std_rgb[1]},Std_B,{std_rgb[2]}\n")
            f.write(f"Entropy_R,{entropy_r:.4f},Entropy_G,{entropy_g:.4f},Entropy_B,{entropy_b:.4f}\n")
            f.write(f"Dominant_Cluster,{dominant_cluster}\n\n")

            f.write("# Cluster Validation Metrics (sampled pixels)\n")
            f.write(f"Inertia,{inertia}\n")
            f.write(f"Silhouette_Score,{silhouette:.4f}\n")
            f.write(f"Calinski_Harabasz_Index,{calinski_harabasz:.4f}\n")
            f.write(f"Davies_Bouldin_Index,{davies_bouldin:.4f}\n\n")

            f.write("# Per-pixel Data\n")
            pixel_df.to_csv(f, index=False)
            f.write("\n# Cluster-level Statistics\n")
            cluster_df.to_csv(f, index=False)

        self.status_label.config(text=f"CSV saved with validation metrics to {filename}")

    def save_csv_button(self):
        csv_name = self.csv_entry.get().strip()
        if not csv_name.lower().endswith(".csv"):
            csv_name += ".csv"
        self.save_csv(csv_name)

    def run_processing(self):
        if self.original_img is None:
            messagebox.showerror("Error", "Select an image first.")
            return
        self.n_clusters = int(self.cluster_entry.get())
        self.count_colors(self.original_img, self.n_clusters)
        self.show_top_colors()
        self.show_3d_plot()
        self.save_csv_button()

    # --- Top Colors ---
    def show_top_colors(self):
        for widget in self.colors_frame.winfo_children():
            widget.destroy()
        colors = [(tuple(self.cluster_centroids[i]), np.sum(self.cluster_labels == i), i)
                  for i in range(self.n_clusters)]
        colors.sort(key=lambda x: x[1], reverse=True)
        for i, (color_tuple, count, cluster_index) in enumerate(colors):
            r, g, b = color_tuple
            color_hex = f"#{r:02x}{g:02x}{b:02x}"
            frame = tk.Frame(self.colors_frame, padx=5, pady=5)
            frame.grid(row=0, column=i)
            swatch = tk.Label(frame, bg=color_hex, width=6, height=3)
            swatch.pack()
            swatch.bind("<Button-1>", lambda e, idx=cluster_index: self.replace_cluster_color(idx))
            tk.Label(frame, text=f"{r},{g},{b}\n{count}", font=("Arial", 8)).pack()

    # --- Replace Cluster Color ---
    def replace_cluster_color(self, cluster_index):
        new_color = colorchooser.askcolor(color=tuple(self.cluster_centroids[cluster_index]))[0]
        if new_color is None:
            return
        rgb = tuple(map(int, new_color))
        self.pixel_array[self.cluster_labels == cluster_index] = rgb
        self.cluster_centroids[cluster_index] = rgb
        self.user_updated_colors[cluster_index] = rgb
        new_img = Image.new("RGB", self.original_img.size)
        new_img.putdata([tuple(p) for p in self.pixel_array])
        self.original_img = new_img
        self.display_image(self.original_img)
        self.show_top_colors()
        self.show_3d_plot()

    # --- 3D Cluster Plot ---
    def show_3d_plot(self):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
        fig = plt.figure(figsize=(4,4))
        ax = fig.add_subplot(111, projection='3d')
        pixels = self.sampled_pixels_for_plot
        colors = pixels / 255.0
        ax.scatter(pixels[:,0], pixels[:,1], pixels[:,2], c=colors, s=5)
        c = self.original_cluster_centroids
        ax.scatter(c[:,0], c[:,1], c[:,2], c=c/255.0, s=100, edgecolors='black')
        for idx, rgb in self.user_updated_colors.items():
            ax.scatter(c[idx,0], c[idx,1], c[idx,2], c=np.array(rgb)/255.0, marker='s', s=100, edgecolors='black', linewidths=1.5)
        handles = [
            plt.Line2D([0],[0], marker='o', color='w', label='Pixel', markerfacecolor='gray', markersize=6),
            plt.Line2D([0],[0], marker='o', color='w', label='Cluster centroid', markerfacecolor='white', markeredgecolor='black', markersize=10)
        ]
        if self.user_updated_colors:
            handles.append(plt.Line2D([0],[0], marker='s', color='w', label='User-edited color', markerfacecolor='red', markeredgecolor='black', markersize=10))
        ax.legend(handles=handles, loc='upper right')
        ax.set_xlabel("R")
        ax.set_ylabel("G")
        ax.set_zlabel("B")
        ax.set_title("RGB Cluster Distribution")
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # --- Reset ---
    def reset_image(self):
        if self.original_pixel_array is None:
            return
        self.pixel_array = self.original_pixel_array.copy()
        self.original_img.putdata([tuple(p) for p in self.pixel_array])
        self.count_colors(self.original_img, self.n_clusters)
        self.display_image(self.original_img)
        self.show_top_colors()
        self.show_3d_plot()
        self.status_label.config(text="Reset complete")

    # --- Save Image ---
    def save_image(self):
        if self.original_img is None:
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".png")
        if file_path:
            self.original_img.save(file_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = ClusteredColorEditor(root)
    root.mainloop()