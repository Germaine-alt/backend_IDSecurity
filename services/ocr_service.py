from typing import List, Dict, Any, Optional
import easyocr
import numpy as np
import json
import os
from rapidfuzz import fuzz
from functools import lru_cache
import logging
from .image_preprocessing import preprocess_for_ocr
from sqlalchemy import select
import re
from sqlalchemy import select
from .text_utils import clean_text_for_matching, contains_digits, normalize_date_str

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class OCRService:
    def __init__(self, langs: List[str] = None, use_gpu: bool = False):
        langs = langs or ['fr', 'en']
        logger.info("Initialisation EasyOCR...")
        self.reader = easyocr.Reader(langs, gpu=use_gpu)
        logger.info("EasyOCR prêt.")
        
    def _load_documents(self, db, DocumentModel):
        logger.info("Chargement des documents (safe mode)...")

        rows = db.session.execute(
            select(
                DocumentModel.id,
                DocumentModel.numero_document,
                DocumentModel.nom,
                DocumentModel.prenom,
                DocumentModel.nationalite,
                DocumentModel.date_de_naissance,
                DocumentModel.date_d_expiration,
                DocumentModel.sexe
            )
        ).all()

        documents = []
        for r in rows:
            documents.append({
                "id": r.id,
                "numero_document": r.numero_document,
                "nom": r.nom,
                "prenom": r.prenom,
                "nationalite": r.nationalite,
                "date_de_naissance": r.date_de_naissance,
                "date_d_expiration": r.date_d_expiration,
                "sexe": r.sexe
            })

        logger.info("Documents chargés: %d", len(documents))
        return documents
 
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

    def fuzzy_match_document(self, text_detected: str, db, DocumentModel, threshold: float = 70.0):
        text_norm = clean_text_for_matching(text_detected)

        docs = self._load_documents(db, DocumentModel)

        fields_weights = {
            "numero_document": 2,
            "nom": 3,
            "prenom": 3,
            "nationalite": 1,
            "date_de_naissance": 1,
            "date_d_expiration": 1
        }

        results = []

        for doc in docs:
            total_score = 0.0
            total_weight = 0.0
            scores_detail = {}

            for field, weight in fields_weights.items():
                val = doc.get(field)
                if not val:
                    continue

                val_norm = clean_text_for_matching(str(val))

                if "date" in field and not contains_digits(text_norm):
                    continue

                score = fuzz.token_set_ratio(text_norm, val_norm)
                scores_detail[field] = score

                total_score += score * weight
                total_weight += weight

            global_score = (total_score / total_weight) if total_weight else 0.0

            if global_score >= threshold:
                results.append({
                    "document_id": doc["id"],
                    "numero_document": doc["numero_document"],
                    "nom": doc["nom"],
                    "prenom": doc["prenom"],
                    "sexe": doc.get("sexe"),
                    "scores_detail": scores_detail,
                    "global_similarity_score": round(global_score, 2)
                })

        results.sort(key=lambda x: x["global_similarity_score"], reverse=True)
        return results

    def extract_externe_fields(self, results):
        """
        Extraction intelligente optimisée pour cartes d'identité togolaises
        """
        nom = None
        prenom = None
        
        # Mots à ignorer (institutions et titres)
        MOTS_IGNORES = [
            'REPUBLIQUE', 'RÉPUBLIQUE', 'RERUBLIQUE', 'TOGOLAISE', 'TOGO',
            'MINISTERE', 'MINISTRE', 'AINISTERE', 'CHARGE', 'SECURITE', 'SÉCURITÉ',
            'CARTE', 'IDENTITE', 'IDENTITÉ', 'NATIONALE', 'NATIONAL',
            'PASSEPORT', 'PERMIS', 'CONDUIRE', 'DOCUMENT',
            'EXPIRE', 'EXPIRATION', 'VALIDE', 'VALIDITE', 'VALIDITÉ',
            'INTERIEUR', 'INTÉRIEUR', 'NUMERO', 'NUMÉRO', 'SEXE',
            'PROFESSION', 'FAIT', 'SIGNATURE', 'NE', 'NÉE'
        ]
        
        # Trier par position verticale (haut -> bas)
        sorted_results = sorted(results, key=lambda r: r["bbox"][0][1])
        
        # Combiner tout le texte pour recherche globale
        full_text = " ".join([r["text"] for r in results])
        full_upper = full_text.upper()
        
        print(f"🔍 Texte OCR complet: {full_text[:200]}...")
        
        # === STRATÉGIE 1 : Recherche par patterns spécifiques ===
        
        # Pattern pour NOM suivi de : et valeur
        nom_match = re.search(r'N[OÔ]M\s*:?\s*([A-ZÀ-Ÿ][A-ZÀ-Ÿ\s\-]{2,30})', full_upper)
        if nom_match:
            candidate = nom_match.group(1).strip()
            # Nettoyer et valider
            candidate = re.sub(r'\s+', ' ', candidate)
            if not any(mot in candidate for mot in MOTS_IGNORES) and len(candidate) > 2:
                nom = candidate
                print(f"✅ Nom trouvé via pattern NOM: {nom}")
        
        # Pattern pour PRENOM suivi de : et valeur
        prenom_match = re.search(r'PR[EÉ]N[OÔ]MS?\s*:?\s*([A-ZÀ-Ÿ][A-Za-zÀ-ÿ\s\-]{2,40})', full_text)
        if prenom_match:
            candidate = prenom_match.group(1).strip()
            candidate = re.sub(r'\s+', ' ', candidate)
            # Accepter majuscules ET minuscules pour prénoms
            if not any(mot in candidate.upper() for mot in MOTS_IGNORES) and len(candidate) > 2:
                prenom = candidate
                print(f"✅ Prénom trouvé via pattern PRENOM: {prenom}")
        
        # === STRATÉGIE 2 : Recherche ligne par ligne ===
        if not nom or not prenom:
            for i, r in enumerate(sorted_results):
                txt = r["text"].strip()
                upper = txt.upper()
                
                # Nettoyer
                clean_txt = re.sub(r'[^A-ZÀ-ÿa-z\s\-]', '', txt).strip()
                
                # Ignorer lignes trop courtes ou avec mots interdits
                if len(clean_txt) < 3:
                    continue
                if any(mot in upper for mot in MOTS_IGNORES):
                    continue
                
                # Chercher label NOM
                if not nom and re.search(r'\bN[OÔ]M\b', upper):
                    # Extraire ce qui suit NOM
                    after_nom = re.sub(r'^.*?N[OÔ]M\s*:?\s*', '', upper).strip()
                    if after_nom and len(after_nom) > 2:
                        # Nettoyer
                        after_nom = re.sub(r'[^A-ZÀ-Ÿ\s\-]', '', after_nom).strip()
                        if not any(mot in after_nom for mot in MOTS_IGNORES):
                            nom = after_nom
                            print(f"✅ Nom trouvé après label: {nom}")
                    
                    # Si rien après le label, regarder ligne suivante
                    elif i + 1 < len(sorted_results):
                        next_txt = sorted_results[i + 1]["text"].strip()
                        next_upper = next_txt.upper()
                        next_clean = re.sub(r'[^A-ZÀ-Ÿ\s\-]', '', next_upper).strip()
                        
                        if (len(next_clean) > 2 and 
                            next_clean.isupper() and
                            not any(mot in next_clean for mot in MOTS_IGNORES)):
                            nom = next_clean
                            print(f"✅ Nom trouvé ligne suivante: {nom}")
                
                # Chercher label PRENOM
                if not prenom and re.search(r'\bPR[EÉ]N[OÔ]MS?\b', upper):
                    # Extraire ce qui suit PRENOM
                    after_prenom = re.sub(r'^.*?PR[EÉ]N[OÔ]MS?\s*:?\s*', '', txt).strip()
                    if after_prenom and len(after_prenom) > 2:
                        # Nettoyer (garder maj/min pour prénoms)
                        after_prenom = re.sub(r'[^A-Za-zÀ-ÿ\s\-]', '', after_prenom).strip()
                        after_prenom = re.sub(r'\s+', ' ', after_prenom)
                        if not any(mot in after_prenom.upper() for mot in MOTS_IGNORES):
                            prenom = after_prenom
                            print(f"✅ Prénom trouvé après label: {prenom}")
                    
                    # Ligne suivante
                    elif i + 1 < len(sorted_results):
                        next_txt = sorted_results[i + 1]["text"].strip()
                        next_clean = re.sub(r'[^A-Za-zÀ-ÿ\s\-]', '', next_txt).strip()
                        next_clean = re.sub(r'\s+', ' ', next_clean)
                        
                        if (len(next_clean) > 2 and
                            not any(mot in next_clean.upper() for mot in MOTS_IGNORES)):
                            prenom = next_clean
                            print(f"✅ Prénom trouvé ligne suivante: {prenom}")
        
        # === STRATÉGIE 3 : Heuristique (si toujours rien) ===
        if not nom or not prenom:
            print("⚠️ Stratégie heuristique activée")
            
            for r in sorted_results:
                txt = r["text"].strip()
                upper = txt.upper()
                clean = re.sub(r'[^A-ZÀ-Ÿ\s\-]', '', upper).strip()
                
                # Conditions pour un NOM potentiel
                if (not nom and 
                    len(clean) >= 3 and 
                    clean.isupper() and 
                    not any(char.isdigit() for char in txt) and
                    not any(mot in clean for mot in MOTS_IGNORES) and
                    not ':' in txt):
                    
                    nom = clean
                    print(f"✅ Nom heuristique: {nom}")
                
                # Conditions pour un PRÉNOM potentiel (peut être en casse mixte)
                elif (not prenom and 
                    len(txt) >= 3 and
                    not any(char.isdigit() for char in txt) and
                    not any(mot in upper for mot in MOTS_IGNORES) and
                    not ':' in txt):
                    
                    clean_prenom = re.sub(r'[^A-Za-zÀ-ÿ\s\-]', '', txt).strip()
                    if len(clean_prenom) >= 3:
                        prenom = clean_prenom
                        print(f"✅ Prénom heuristique: {prenom}")
        
        # Normaliser les résultats
        if nom:
            nom = ' '.join(nom.split())
            # Capitaliser proprement le nom
            nom = nom.upper()
        
        if prenom:
            prenom = ' '.join(prenom.split())
            # Capitaliser proprement le prénom (première lettre de chaque mot)
            prenom = ' '.join(word.capitalize() for word in prenom.split())
        
        print(f"📝 Résultat final - Nom: {nom}, Prénom: {prenom}")
        
        return {
            "nom": nom,
            "prenom": prenom
        }
    

    