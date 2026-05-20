# HDR Fusion - Multi Exposure Fusion (MEF)

## 1.Giới thiệu

Project này thực hiện:

```text
Multi Exposure Fusion (MEF)
```

ghép nhiều ảnh có exposure khác nhau để tạo ảnh đầu ra có dynamic range tốt hơn và nhìn giống HDR.

Pipeline sử dụng:

```text
OpenCV MergeMertens
```

---

## 2.Bài toán

Input:

- 5 ảnh cùng một scene
- khác exposure
- khác độ sáng

Ví dụ:

```text
0.png
1.png
2.png
3.png
4.png
```

Output:

```text
scene_xxxx.png
```

Ảnh HDR-like sau khi fusion.

---

## 3.Cấu trúc thư mục

```text
HDR_Fusion/
│
├── dataset_scene/
│    ├── scene_0000/
│    │    ├── 0.png
│    │    ├── 1.png
│    │    ├── 2.png
│    │    ├── 3.png
│    │    └── 4.png
│    │
│    ├── scene_0001/
│
├── output/
│
├── auto_convert.py
├── mef_fusion.py
├── requirements.txt
└── README.md
```

---

## 4.Cài đặt

### 4.1.Cài Python

Khuyên dùng:

```text
Python 3.10+
```

Tải tại:

https://www.python.org/downloads/

Khi cài nhớ tick:

```text
Add Python to PATH
```

---

### 4.2.Cài package

Mở terminal trong VS Code:

```bash
pip install -r requirements.txt
```

Hoặc:

```bash
pip install opencv-python==4.8.1.78 numpy==1.26.4 rawpy imageio matplotlib
```

---

## 5.Chuyển RAW/JPG/PNG về PNG

Project hỗ trợ:

### RAW
- CR2
- CR3
- NEF
- ARW
- DNG
- RAF
- RW2

### IMAGE
- JPG
- JPEG
- PNG
- BMP
- TIFF

Chạy:

```bash
python auto_convert.py
```

Sau khi chạy:

```text
dataset_scene/
```

sẽ chứa toàn bộ ảnh PNG.

---

## 6.Chạy HDR Fusion (MEF)

Chạy:

```bash
python mef_fusion.py
```

---

## 7.Kết quả

Ảnh output sẽ nằm trong:

```text
output/
```

Ví dụ:

```text
output/
 ├── scene_0000.png
 ├── scene_0001.png
 └── ...
```

---

## 8.Thuật toán sử dụng

Project sử dụng:

```python
cv2.createMergeMertens()
```

Đây là thuật toán:

```text
Exposure Fusion / MEF
```

dùng để:
- recover shadow
- giảm cháy sáng
- tăng dynamic range
- tạo HDR-like image

---

## 9.Pipeline

```text
RAW/JPG/PNG
↓
Convert PNG
↓
Multi Exposure Fusion (MEF)
↓
HDR-like image
```

---


## 10.Kết quả đạt được

- Ghép nhiều exposure thành ảnh HDR-like
- Giảm mất chi tiết vùng sáng
- Tăng chi tiết vùng tối
- Cải thiện dynamic range
