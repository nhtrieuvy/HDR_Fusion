import os
import cv2
import numpy as np

# =========================
# DATASET PATH
# =========================

dataset_path = "dataset_scene"

output_path = "output"

os.makedirs(output_path, exist_ok=True)

# =========================
# LOAD SCENES
# =========================

scenes = sorted(os.listdir(dataset_path))

print("Total scenes:", len(scenes))

# =========================
# CREATE MEF
# =========================

merge = cv2.createMergeMertens()

# =========================
# PROCESS ALL SCENES
# =========================

for scene_name in scenes:

    print("\nProcessing:", scene_name)

    scene_path = os.path.join(
        dataset_path,
        scene_name
    )

    files = sorted(os.listdir(scene_path))

    imgs = []

    # =========================
    # READ IMAGES
    # =========================

    for file in files:

        path = os.path.join(
            scene_path,
            file
        )

        img = cv2.imread(
            path,
            cv2.IMREAD_UNCHANGED
        )

        if img is None:

            print("Cannot read:", path)
            continue

        img = cv2.cvtColor(
            img,
            cv2.COLOR_BGR2RGB
        )

        imgs.append(img)

    # =========================
    # CHECK IMAGE COUNT
    # =========================

    if len(imgs) < 2:

        print("Skip scene:", scene_name)
        continue

    # =========================
    # MEF FUSION
    # =========================

    fusion = merge.process(imgs)

    # =========================
    # REMOVE NEGATIVE
    # =========================

    fusion = np.clip(
        fusion,
        0,
        1
    )

    # =========================
    # NORMALIZE
    # =========================

    fusion = cv2.normalize(
        fusion,
        None,
        0,
        1,
        cv2.NORM_MINMAX
    )

    # =========================
    # GAMMA
    # =========================

    fusion = np.power(
        fusion,
        0.95
    )

    # =========================
    # FLOAT -> UINT8
    # =========================

    fusion_8bit = (
        fusion * 255
    ).astype(np.uint8)

    # =========================
    # SAVE OUTPUT
    # =========================

    save_path = os.path.join(
        output_path,
        scene_name + ".png"
    )

    cv2.imwrite(
        save_path,
        cv2.cvtColor(
            fusion_8bit,
            cv2.COLOR_RGB2BGR
        )
    )

    print("Saved:", save_path)

print("\nDONE")