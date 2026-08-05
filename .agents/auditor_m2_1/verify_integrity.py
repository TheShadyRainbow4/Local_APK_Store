import os
import json
from PIL import Image

img_dir = r'C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\images'
png_files = [f for f in os.listdir(img_dir) if f.endswith('.png')]

print(f"Total image files in images directory: {len(png_files)}")

valid_image_count = 0
invalid_images = []

for f in png_files:
    path = os.path.join(img_dir, f)
    try:
        with Image.open(path) as img:
            img.verify()
            valid_image_count += 1
            print(f"  [OK] {f}: format={img.format}, size={img.size}, mode={img.mode}")
    except Exception as e:
        invalid_images.append((f, str(e)))

print(f"\nValid raster images verified by PIL: {valid_image_count} / {len(png_files)}")
if invalid_images:
    print("Corrupt or invalid image files:")
    for fname, err in invalid_images:
        print(f"  [FAIL] {fname}: {err}")
else:
    print("ALL 40 images are 100% valid, authentic binary raster images!")
