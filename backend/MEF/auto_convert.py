import os
import cv2
import rawpy
import numpy as np

# =========================
# PATH
# =========================

input_path = "raw_dataset"

output_path = "dataset_scene"

os.makedirs(output_path, exist_ok=True)

# =========================
# RAW EXTENSIONS
# =========================

RAW_EXTENSIONS = [
    "cr2",
    "cr3",
    "nef",
    "arw",
    "dng",
    "raf",
    "rw2"
]

# =========================
# NORMAL IMAGE EXTENSIONS
# =========================

IMAGE_EXTENSIONS = [
    "jpg",
    "jpeg",
    "png",
    "bmp",
    "tif",
    "tiff"
]

# =========================
# READ IMAGE
# =========================

def read_image(path):

    ext = path.lower().split(".")[-1]

    # =========================
    # RAW IMAGE
    # =========================

    if ext in RAW_EXTENSIONS:

        with rawpy.imread(path) as raw:

            img = raw.postprocess(

                # giữ white balance camera
                use_camera_wb=True,

                # full resolution
                half_size=False,

                # QUAN TRỌNG:
                # không auto kéo sáng
                no_auto_bright=True,

                # output 16bit
                output_bps=16
            )

    # =========================
    # NORMAL IMAGE
    # =========================

    elif ext in IMAGE_EXTENSIONS:

        img = cv2.imread(
            path,
            cv2.IMREAD_UNCHANGED
        )

        if img is None:
            return None

        img = cv2.cvtColor(
            img,
            cv2.COLOR_BGR2RGB
        )

    else:

        return None

    return img

# =========================
# COMPUTE BRIGHTNESS
# =========================

def compute_brightness(img):

    gray = cv2.cvtColor(
        img.astype(np.float32),
        cv2.COLOR_RGB2GRAY
    )

    brightness = np.mean(gray)

    return brightness

# =========================
# LOAD SCENES
# =========================

scenes = sorted(os.listdir(input_path))

print("Total scenes:", len(scenes))

# =========================
# PROCESS SCENES
# =========================

for scene_name in scenes:

    scene_input = os.path.join(
        input_path,
        scene_name
    )

    if not os.path.isdir(scene_input):
        continue

    scene_output = os.path.join(
        output_path,
        scene_name
    )

    os.makedirs(scene_output, exist_ok=True)

    files = sorted(os.listdir(scene_input))

    image_data = []

    print("\n=========================")
    print("SCENE:", scene_name)
    print("=========================")

    # =========================
    # READ ALL IMAGES
    # =========================

    for file in files:

        path = os.path.join(
            scene_input,
            file
        )

        print("Reading:", path)

        img = read_image(path)

        if img is None:

            print("Skipped:", file)
            continue

        brightness = compute_brightness(img)

        print(
            f"Brightness = {brightness:.2f}"
        )

        image_data.append({

            "file": file,
            "img": img,
            "brightness": brightness

        })

    # =========================
    # SORT DARK -> BRIGHT
    # =========================

    image_data.sort(
        key=lambda x: x["brightness"]
    )

    print("\nExposure order:")

    for idx, data in enumerate(image_data):

        print(
            idx,
            data["file"],
            "brightness =",
            round(data["brightness"], 2)
        )

    # =========================
    # SAVE PNG
    # =========================

    for idx, data in enumerate(image_data):

        save_path = os.path.join(
            scene_output,
            f"{idx}.png"
        )

        img_rgb = data["img"]

        # =========================
        # UINT16 -> UINT8
        # =========================

        if img_rgb.dtype == np.uint16:

            img_rgb = (
                img_rgb / 256
            ).astype(np.uint8)

        # =========================
        # RGB -> BGR
        # =========================

        img_bgr = cv2.cvtColor(
            img_rgb,
            cv2.COLOR_RGB2BGR
        )

        # =========================
        # SAVE PNG
        # =========================

        cv2.imwrite(
            save_path,
            img_bgr
        )

        print("Saved:", save_path)

print("\nDONE")