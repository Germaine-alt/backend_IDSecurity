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
        Extraction précise du nom et prénom pour documents externes
        Utilise plusieurs stratégies : patterns, positions spatiales, et validation stricte
        """
        nom = None
        prenom = None
        
        # Filtrer les résultats avec faible confiance (< 0.5)
        filtered_results = [r for r in results if r.get("confidence", 0) >= 0.5]
        if not filtered_results:
            filtered_results = results  # Fallback si tous ont faible confiance
        
        # Mots à ignorer (institutions et titres)
        MOTS_IGNORES = [
            'REPUBLIQUE', 'RÉPUBLIQUE', 'RERUBLIQUE', 'TOGOLAISE', 'TOGO',
            'MINISTERE', 'MINISTRE', 'AINISTERE', 'CHARGE', 'SECURITE', 'SÉCURITÉ',
            'CARTE', 'IDENTITE', 'IDENTITÉ', 'NATIONALE', 'NATIONAL',
            'PASSEPORT', 'PERMIS', 'CONDUIRE', 'DOCUMENT',
            'EXPIRE', 'EXPIRATION', 'VALIDE', 'VALIDITE', 'VALIDITÉ',
            'INTERIEUR', 'INTÉRIEUR', 'NUMERO', 'NUMÉRO', 'SEXE',
            'PROFESSION', 'FAIT', 'SIGNATURE', 'NE', 'NÉE', 'NAME', 'SURNAME',
            'BIRTH', 'DATE', 'BORN', 'NATIONALITY', 'NATIONALITÉ'
        ]
        
        # Labels possibles pour NOM et PRENOM
        NOM_LABELS = [r'N[OÔ]M', r'NAME', r'SURNAME', r'FAMILY\s*NAME', r'LAST\s*NAME']
        PRENOM_LABELS = [r'PR[EÉ]N[OÔ]MS?', r'FIRST\s*NAME', r'GIVEN\s*NAME', r'FORENAME']
        
        # Trier par position verticale (haut -> bas) puis horizontale (gauche -> droite)
        sorted_results = sorted(filtered_results, key=lambda r: (r["bbox"][0][1], r["bbox"][0][0]))
        
        # Combiner tout le texte pour recherche globale
        full_text = " ".join([r["text"] for r in filtered_results])
        full_upper = full_text.upper()
        
        print(f"🔍 Texte OCR complet: {full_text[:300]}...")
        print(f"📊 {len(filtered_results)} résultats filtrés (confiance >= 0.5)")
        
        def is_valid_name(text, is_nom=True):
            """Valide si un texte est un nom/prénom valide"""
            if not text or len(text.strip()) < 2:
                return False
            
            # Ne doit pas contenir de chiffres
            if re.search(r'\d', text):
                return False
            
            # Ne doit pas être une date
            if re.search(r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}', text):
                return False
            
            # Ne doit pas contenir de mots interdits
            text_upper = text.upper()
            if any(mot in text_upper for mot in MOTS_IGNORES):
                return False
            
            # Ne doit pas être trop court après nettoyage
            clean = re.sub(r'[^A-Za-zÀ-ÿ\s\-]', '', text).strip()
            if len(clean) < 2:
                return False
            
            # Pour NOM : généralement en majuscules
            if is_nom:
                # Accepter si majoritairement en majuscules
                upper_count = sum(1 for c in clean if c.isupper())
                if len(clean.replace(' ', '').replace('-', '')) > 0:
                    upper_ratio = upper_count / len(clean.replace(' ', '').replace('-', ''))
                    if upper_ratio < 0.5:  # Moins de 50% en majuscules
                        return False
            
            return True
        
        def extract_after_label(text, label_pattern, is_nom=True):
            """Extrait la valeur après un label (NOM, PRENOM, etc.)"""
            # Pattern pour capturer le label suivi de : ou espace et la valeur
            patterns = [
                rf'{label_pattern}\s*[:]\s*([A-Za-zÀ-ÿ\s\-]+)',
                rf'{label_pattern}\s+([A-Za-zÀ-ÿ\s\-]+)',
                rf'{label_pattern}\s*[:]\s*([A-ZÀ-Ÿ\s\-]+)',  # Pour NOM en majuscules
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    candidate = match.group(1).strip()
                    # Nettoyer
                    if is_nom:
                        candidate = re.sub(r'[^A-ZÀ-Ÿ\s\-]', '', candidate.upper()).strip()
                    else:
                        candidate = re.sub(r'[^A-Za-zÀ-ÿ\s\-]', '', candidate).strip()
                    candidate = re.sub(r'\s+', ' ', candidate)
                    
                    if is_valid_name(candidate, is_nom=is_nom):
                        return candidate
            return None
        
        # === STRATÉGIE 1 : Recherche par patterns globaux améliorés ===
        for nom_label in NOM_LABELS:
            if not nom:
                candidate = extract_after_label(full_upper, nom_label, is_nom=True)
                if candidate:
                    nom = candidate
                    print(f"✅ Nom trouvé via pattern global {nom_label}: {nom}")
                    break
        
        for prenom_label in PRENOM_LABELS:
            if not prenom:
                candidate = extract_after_label(full_text, prenom_label, is_nom=False)
                if candidate:
                    prenom = candidate
                    print(f"✅ Prénom trouvé via pattern global {prenom_label}: {prenom}")
                    break
        
        # === STRATÉGIE 2 : Recherche ligne par ligne avec positions spatiales ===
        if not nom or not prenom:
            nom_index = None
            prenom_index = None
            
            for i, r in enumerate(sorted_results):
                txt = r["text"].strip()
                upper = txt.upper()
                y_pos = r["bbox"][0][1]  # Position Y (verticale)
                
                # Chercher label NOM
                if not nom:
                    for nom_label in NOM_LABELS:
                        if re.search(nom_label, upper, re.IGNORECASE):
                            nom_index = i
                            # Extraire depuis la même ligne
                            candidate = extract_after_label(txt, nom_label, is_nom=True)
                            if candidate:
                                nom = candidate
                                print(f"✅ Nom trouvé ligne {i} via label: {nom}")
                                break
                            
                            # Si rien sur la même ligne, chercher ligne suivante
                            if i + 1 < len(sorted_results):
                                next_r = sorted_results[i + 1]
                                next_y = next_r["bbox"][0][1]
                                # Vérifier que la ligne suivante est proche verticalement (max 50px)
                                if abs(next_y - y_pos) < 50:
                                    next_txt = next_r["text"].strip()
                                    next_clean = re.sub(r'[^A-ZÀ-Ÿ\s\-]', '', next_txt.upper()).strip()
                                    next_clean = re.sub(r'\s+', ' ', next_clean)
                                    if is_valid_name(next_clean, is_nom=True):
                                        nom = next_clean
                                        print(f"✅ Nom trouvé ligne suivante {i+1}: {nom}")
                                        break
                
                # Chercher label PRENOM
                if not prenom:
                    for prenom_label in PRENOM_LABELS:
                        if re.search(prenom_label, upper, re.IGNORECASE):
                            prenom_index = i
                            # Extraire depuis la même ligne
                            candidate = extract_after_label(txt, prenom_label, is_nom=False)
                            if candidate:
                                prenom = candidate
                                print(f"✅ Prénom trouvé ligne {i} via label: {prenom}")
                                break
                            
                            # Si rien sur la même ligne, chercher ligne suivante
                            if i + 1 < len(sorted_results):
                                next_r = sorted_results[i + 1]
                                next_y = next_r["bbox"][0][1]
                                # Vérifier que la ligne suivante est proche verticalement
                                if abs(next_y - y_pos) < 50:
                                    next_txt = next_r["text"].strip()
                                    next_clean = re.sub(r'[^A-Za-zÀ-ÿ\s\-]', '', next_txt).strip()
                                    next_clean = re.sub(r'\s+', ' ', next_clean)
                                    if is_valid_name(next_clean, is_nom=False):
                                        prenom = next_clean
                                        print(f"✅ Prénom trouvé ligne suivante {i+1}: {prenom}")
                                        break
            
            # Si on a trouvé NOM mais pas PRENOM (ou vice versa), chercher proche spatialement
            if nom_index is not None and not prenom:
                # Chercher PRENOM près du NOM (dans les 3 lignes suivantes)
                for i in range(nom_index + 1, min(nom_index + 4, len(sorted_results))):
                    r = sorted_results[i]
                    txt = r["text"].strip()
                    clean = re.sub(r'[^A-Za-zÀ-ÿ\s\-]', '', txt).strip()
                    clean = re.sub(r'\s+', ' ', clean)
                    if is_valid_name(clean, is_nom=False) and len(clean) >= 3:
                        prenom = clean
                        print(f"✅ Prénom trouvé près du NOM (ligne {i}): {prenom}")
                        break
            
            if prenom_index is not None and not nom:
                # Chercher NOM près du PRENOM (dans les 3 lignes précédentes ou suivantes)
                for i in range(max(0, prenom_index - 3), min(prenom_index + 4, len(sorted_results))):
                    if i == prenom_index:
                        continue
                    r = sorted_results[i]
                    txt = r["text"].strip()
                    clean = re.sub(r'[^A-ZÀ-Ÿ\s\-]', '', txt.upper()).strip()
                    clean = re.sub(r'\s+', ' ', clean)
                    if is_valid_name(clean, is_nom=True) and len(clean) >= 3:
                        nom = clean
                        print(f"✅ Nom trouvé près du PRENOM (ligne {i}): {nom}")
                        break
        
        # === STRATÉGIE 3 : Détection de format "NOM PRENOM" sur une même ligne ===
        if not nom or not prenom:
            for r in sorted_results:
                txt = r["text"].strip()
                # Pattern pour "NOM PRENOM" ou "NOM, PRENOM" ou "NOM : PRENOM"
                # Chercher deux mots/phrases séparés
                parts = re.split(r'[,\s:]+', txt)
                if len(parts) >= 2:
                    # Premier élément comme NOM potentiel
                    if not nom:
                        candidate_nom = re.sub(r'[^A-ZÀ-Ÿ\s\-]', '', parts[0].upper()).strip()
                        candidate_nom = re.sub(r'\s+', ' ', candidate_nom)
                        if is_valid_name(candidate_nom, is_nom=True) and len(candidate_nom) >= 3:
                            nom = candidate_nom
                            print(f"✅ Nom trouvé via format combiné: {nom}")
                    
                    # Deuxième élément comme PRENOM potentiel
                    if not prenom and len(parts) >= 2:
                        candidate_prenom = re.sub(r'[^A-Za-zÀ-ÿ\s\-]', '', parts[1]).strip()
                        candidate_prenom = re.sub(r'\s+', ' ', candidate_prenom)
                        if is_valid_name(candidate_prenom, is_nom=False) and len(candidate_prenom) >= 3:
                            prenom = candidate_prenom
                            print(f"✅ Prénom trouvé via format combiné: {prenom}")
        
        # === STRATÉGIE 4 : Heuristique améliorée (dernier recours) ===
        if not nom or not prenom:
            print("⚠️ Stratégie heuristique activée")
            
            # Trier par confiance décroissante pour prioriser les résultats fiables
            sorted_by_conf = sorted(filtered_results, key=lambda r: r.get("confidence", 0), reverse=True)
            
            for r in sorted_by_conf:
                txt = r["text"].strip()
                upper = txt.upper()
                clean_upper = re.sub(r'[^A-ZÀ-Ÿ\s\-]', '', upper).strip()
                clean_mixed = re.sub(r'[^A-Za-zÀ-ÿ\s\-]', '', txt).strip()
                
                # NOM : majuscules, pas de chiffres, pas de mots interdits
                if (not nom and 
                    len(clean_upper) >= 3 and 
                    clean_upper.isupper() and
                    is_valid_name(clean_upper, is_nom=True)):
                    nom = clean_upper
                    print(f"✅ Nom heuristique: {nom}")
                
                # PRENOM : casse mixte possible, pas de chiffres
                if (not prenom and 
                    len(clean_mixed) >= 3 and
                    is_valid_name(clean_mixed, is_nom=False)):
                    prenom = clean_mixed
                    print(f"✅ Prénom heuristique: {prenom}")
                
                if nom and prenom:
                    break
        
        # Normaliser les résultats finaux
        if nom:
            nom = ' '.join(nom.split())
            nom = nom.upper()
            # Validation finale
            if not is_valid_name(nom, is_nom=True):
                nom = None
        
        if prenom:
            prenom = ' '.join(prenom.split())
            # Capitaliser proprement (première lettre de chaque mot)
            prenom = ' '.join(word.capitalize() for word in prenom.split())
            # Validation finale
            if not is_valid_name(prenom, is_nom=False):
                prenom = None
        
        print(f"📝 Résultat final - Nom: {nom}, Prénom: {prenom}")
        
        return {
            "nom": nom,
            "prenom": prenom
        }
    

    