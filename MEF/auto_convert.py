import os
import cv2
import rawpy
import imageio

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
# IMAGE EXTENSIONS
# =========================

IMAGE_EXTENSIONS = [
    "jpg",
    "jpeg",
    "png",
    "bmp",
    "tif",
    "tiff"
]

scenes = sorted(os.listdir(input_path))

for scene_name in scenes:

    scene_input = os.path.join(
        input_path,
        scene_name
    )

    scene_output = os.path.join(
        output_path,
        scene_name
    )

    os.makedirs(scene_output, exist_ok=True)

    files = sorted(os.listdir(scene_input))

    for i, file in enumerate(files):

        path = os.path.join(
            scene_input,
            file
        )

        ext = file.lower().split(".")[-1]

        print("Reading:", path)

        # =========================
        # RAW FILE
        # =========================

        if ext in RAW_EXTENSIONS:

            with rawpy.imread(path) as raw:

                img = raw.postprocess(
                    use_camera_wb=True,
                    half_size=False,
                    no_auto_bright=False,
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

            img = cv2.cvtColor(
                img,
                cv2.COLOR_BGR2RGB
            )

        else:

            print("Skipped unsupported:", file)
            continue

        # =========================
        # SAVE PNG
        # =========================

        save_path = os.path.join(
            scene_output,
            f"{i}.png"
        )

        imageio.imwrite(
            save_path,
            img
        )

        print("Saved:", save_path)