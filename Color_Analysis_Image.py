from PIL import Image
from collections import Counter
from sys import exit, argv
import csv

def count_colors(image_path, output_file):
    # Open image
    img = Image.open(image_path)

    # Ensure image is in RGB mode
    img = img.convert("RGB")

    # Get all pixels
    pixels = list(img.getdata())

    # Count occurrences of each RGB color
    color_counts = Counter(pixels)

    # Sort by most common first
    sorted_colors = color_counts.most_common()

    # Write to CSV file
    with open(output_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["R", "G", "B", "Count"])

        for (r, g, b), count in sorted_colors:
            writer.writerow([r, g, b, count])

    print(f"Saved results to {output_file}")


if __name__ == "__main__":
    if len(argv) != 3:
        print("Usage: python color_counter.py input_image output.csv")
        exit(1)

    input_image = argv[1]
    output_file = argv[2]

    count_colors(input_image, output_file)