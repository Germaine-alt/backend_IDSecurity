from typing import Optional
import cv2
import numpy as np

def adaptive_resize(image: np.ndarray, max_dim: int = 1600, upscale_factor: float = 2.2) -> np.ndarray:
    """
    Redimensionne l'image si elle est trop petite ou trop grande.
    - Si plus petite que max_dim on upscale par upscale_factor.
    - Si très grande, on la réduit pour limiter le coût.
    """
    h, w = image.shape[:2]
    max_side = max(h, w)

    if max_side < 800:
        # petite image -> agrandir légèrement
        image = cv2.resize(image, None, fx=upscale_factor, fy=upscale_factor, interpolation=cv2.INTER_CUBIC)
    elif max_side > max_dim:
        scale = max_dim / max_side
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    return image


def preprocess_for_ocr(image_path: str, use_clahe: bool = True) -> np.ndarray:
    """
    Pipeline optimisé de prétraitement.
    Retourne une image binaire (numpy.ndarray) prête pour l'OCR.
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image introuvable: {image_path}")

    image = adaptive_resize(image)

    # convertir en gris
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # denoise (param modéré pour ne pas perdre de traits fins)
    gray = cv2.fastNlMeansDenoising(gray, h=20)

    # contraste adaptatif
    if use_clahe:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

    # léger flou pour réduire le bruit d'impulsion
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # seuillage adaptatif plus conservateur (ou OTSU si conditions)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        21, 8
    )

    # fermeture pour combler petits trous
    kernel = np.ones((2, 2), np.uint8)
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return morph
