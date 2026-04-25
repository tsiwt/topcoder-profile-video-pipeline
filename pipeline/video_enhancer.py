"""
Per-frame video enhancement using OpenCV (FAST version):
  - auto white-balance
  - brightness / contrast / saturation boost
  - light Gaussian denoise
  - NO face detection (Haar cascade per-frame is too slow)
"""
import cv2
import numpy as np


def auto_white_balance(img: np.ndarray) -> np.ndarray:
    """Simple gray-world white balance."""
    result = img.copy().astype(np.float32)
    avg_b = np.mean(result[:, :, 0])
    avg_g = np.mean(result[:, :, 1])
    avg_r = np.mean(result[:, :, 2])
    avg_gray = (avg_b + avg_g + avg_r) / 3.0
    if avg_b > 0:
        result[:, :, 0] *= avg_gray / avg_b
    if avg_g > 0:
        result[:, :, 1] *= avg_gray / avg_g
    if avg_r > 0:
        result[:, :, 2] *= avg_gray / avg_r
    return np.clip(result, 0, 255).astype(np.uint8)


def adjust_brightness_contrast(img, brightness=10, contrast=1.15):
    """Apply brightness and contrast."""
    result = img.astype(np.float32)
    result = result * contrast + brightness
    return np.clip(result, 0, 255).astype(np.uint8)


def boost_saturation(img, factor=1.2):
    """Increase colour saturation."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] *= factor
    hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def enhance_frame(frame: np.ndarray) -> np.ndarray:
    """
    MoviePy fl_image callback - receives RGB, must return RGB.
    Fast path: color correction only, no per-frame face detection.
    """
    bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    bgr = auto_white_balance(bgr)
    bgr = adjust_brightness_contrast(bgr, brightness=8, contrast=1.12)
    bgr = boost_saturation(bgr, factor=1.15)
    bgr = cv2.GaussianBlur(bgr, (3, 3), 0)

    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
