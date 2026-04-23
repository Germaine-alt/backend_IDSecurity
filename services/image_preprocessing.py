from typing import Optional
import cv2
import numpy as np

def adaptive_resize(image: np.ndarray, max_dim: int = 1400, upscale_factor: float = 1.8) -> np.ndarray:
    """
    Redimensionne intelligemment
    """
    h, w = image.shape[:2]
    max_side = max(h, w)

    # ✅ Upscale si trop petite (critique pour l'OCR)
    if max_side < 700:
        image = cv2.resize(image, None, fx=upscale_factor, fy=upscale_factor, 
                          interpolation=cv2.INTER_CUBIC)
    # ✅ Downscale si énorme
    elif max_side > max_dim:
        scale = max_dim / max_side
        image = cv2.resize(image, None, fx=scale, fy=scale, 
                          interpolation=cv2.INTER_AREA)
    
    return image


def preprocess_for_ocr(image_path: str, use_clahe: bool = True) -> np.ndarray:
    """
    Pipeline ÉQUILIBRÉ : rapide + précis
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image introuvable: {image_path}")

    # ✅ Resize adaptatif
    image = adaptive_resize(image)

    # ✅ Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # ✅ CLAHE pour le contraste (rapide et efficace)
    if use_clahe:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

    # ✅ Léger denoising (version RAPIDE)
    gray = cv2.fastNlMeansDenoising(gray, h=10)  # h=10 au lieu de 20

    # ✅ Flou léger
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # ✅ Seuillage adaptatif (meilleur qu'OTSU pour documents variés)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11,  # ✅ Réduit de 21 → 11 (plus rapide)
        C=5
    )

    # ✅ Morphologie minimale
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return thresh










