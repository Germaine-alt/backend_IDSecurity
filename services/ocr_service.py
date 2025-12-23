from typing import List, Dict, Any
import easyocr
import numpy as np
import json
import os
from rapidfuzz import fuzz
from functools import lru_cache
import logging
from .image_preprocessing import preprocess_for_ocr
from .text_utils import clean_text_for_matching, contains_digits, normalize_date_str

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class OCRService:
    def __init__(self, langs: List[str] = None, use_gpu: bool = False):
        langs = langs or ['fr', 'en']
        logger.info("Initialisation EasyOCR...")
        self.reader = easyocr.Reader(langs, gpu=use_gpu)
        logger.info("EasyOCR prêt.")
        # cache des documents en mémoire pour éviter hits DB répétés
        self._docs_cache = None

    def _load_documents(self, DocumentModel):
        """
        Charge la table Document en mémoire (cache).
        DocumentModel doit être le modèle SQLAlchemy.
        """
        if self._docs_cache is None:
            logger.info("Chargement des documents en cache...")
            self._docs_cache = DocumentModel.query.all()
            logger.info("Documents chargés: %d", len(self._docs_cache))
        return self._docs_cache

    def process_image(self, image_path: str, preprocess: bool = True) -> List[Dict[str, Any]]:
        """
        Lance le pipeline OCR sur l'image et renvoie une liste de dicts:
        { bbox, text, confidence }
        """
        if preprocess:
            img = preprocess_for_ocr(image_path)
        else:
            import cv2
            img = cv2.imread(image_path)
            if img is None:
                raise FileNotFoundError(image_path)

        # EasyOCR accepte numpy arrays en niveaux de gris ou BGR
        results = self.reader.readtext(img, detail=1, paragraph=False)

        # normaliser la sortie
        normalized = []
        for bbox, text, conf in results:
            normalized.append({
                "bbox": [[int(p[0]), int(p[1])] for p in bbox],
                "text": text.strip(),
                "confidence": float(conf)
            })
        return normalized

    def annotate_image(self, image_path: str, results: List[Dict[str, Any]], output_dir: str = "public/results") -> str:
        import cv2
        os.makedirs(output_dir, exist_ok=True)
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(image_path)

        for res in results:
            pts = np.array(res['bbox'], dtype=np.int32)
            cv2.polylines(image, [pts], True, (0, 255, 0), 2)
            # Placer le texte légèrement en dehors du bbox pour meilleure lisibilité
            x, y = pts[0]
            cv2.putText(image, res['text'], (x, max(y - 6, 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        out_path = os.path.join(output_dir, f"annotated_{os.path.basename(image_path)}")
        cv2.imwrite(out_path, image)
        return out_path

    def save_result_to_db(self, db, OCRResultModel, filename: str, results: List[Dict[str, Any]], annotated_path: str):
        full_text = " ".join([r["text"] for r in results])
        max_conf = max([r["confidence"] for r in results]) if results else 0.0
        entry = OCRResultModel(
            image_name=filename,
            text_detected=full_text,
            confidence=max_conf,
            bbox=json.dumps(results, ensure_ascii=False),
            annotated_image=annotated_path
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    def fuzzy_match_document(self, text_detected: str, DocumentModel, threshold: float = 70.0) -> List[Dict[str, Any]]:
        """
        Compare le texte détecté avec les documents en base via fuzzy matching pondéré.
        DocumentModel: modèle SQLAlchemy Document
        """
        text_norm = clean_text_for_matching(text_detected)
        docs = self._load_documents(DocumentModel)

        results = []

        # définir champs et poids une seule fois
        fields_weights = {
            "numero_document": 2,
            "nom": 3,
            "prenom": 3,
            "nationalite": 1,
            "date_de_naissance": 1,
            "date_d_expiration": 1
        }

        for doc in docs:
            total_score = 0.0
            total_weight = 0.0
            scores_detail = {}

            # parcourir champs
            for field, weight in fields_weights.items():
                val = getattr(doc, field, None)
                if not val:
                    continue

                val_norm = clean_text_for_matching(str(val))
                # si champ date et l'OCR ne contient pas de chiffres => skip
                if "date" in field and not contains_digits(text_norm):
                    continue

                score = fuzz.token_set_ratio(text_norm, val_norm)
                scores_detail[field] = score
                total_score += score * weight
                total_weight += weight

            global_score = (total_score / total_weight) if total_weight > 0 else 0.0
            if global_score >= threshold:
                results.append({
                    "document_id": doc.id,
                    "numero_document": doc.numero_document,
                    "nom": doc.nom,
                    "prenom": doc.prenom,
                    "sexe": getattr(doc, "sexe", None),
                    "scores_detail": scores_detail,
                    "global_similarity_score": round(global_score, 2)
                })

        # trier par meilleur score
        results.sort(key=lambda x: x["global_similarity_score"], reverse=True)
        return results
