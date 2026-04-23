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
        self._documents_cache = None  # ✅ NOUVEAU
        self._cache_time = 0
        
    def _load_documents(self, db, DocumentModel):
        import time
        current_time = time.time()
        
        # ✅ Cache de 60 secondes
        if self._documents_cache and (current_time - self._cache_time < 60):
            logger.info("📦 Utilisation cache documents")
            return self._documents_cache
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
            # ✅ Mise en cache
        self._documents_cache = documents
        self._cache_time = current_time

        logger.info("Documents chargés: %d", len(documents))
        return documents
 
    # def process_image(self, image_path: str, preprocess: bool = True) -> List[Dict[str, Any]]:
    #     """
    #     Lance le pipeline OCR sur l'image et renvoie une liste de dicts:
    #     { bbox, text, confidence }
    #     """
    #     if preprocess:
    #         img = preprocess_for_ocr(image_path)
    #     else:
    #         import cv2
    #         img = cv2.imread(image_path)
    #         if img is None:
    #             raise FileNotFoundError(image_path)

        
    #     results = self.reader.readtext(img, detail=1, paragraph=False,)

    #     # normaliser la sortie
    #     normalized = []
    #     for bbox, text, conf in results:
    #         normalized.append({
    #             "bbox": [[int(p[0]), int(p[1])] for p in bbox],
    #             "text": text.strip(),
    #             "confidence": float(conf)
    #         })
    #     return normalized


    def process_image(self, image_path: str, preprocess: bool = True) -> List[Dict[str, Any]]:
        if preprocess:
            img = preprocess_for_ocr(image_path)
        else:
            import cv2
            img = cv2.imread(image_path)
            if img is None:
                raise FileNotFoundError(image_path)

        # ✅ Paramètres optimisés
        results = self.reader.readtext(
            img, 
            detail=1, 
            paragraph=False,
            batch_size=4,        # ✅ NOUVEAU : traitement par batch (GPU)
            decoder='greedy',    # ✅ NOUVEAU : décodage rapide
            beamWidth=3,         # ✅ NOUVEAU : réduit la recherche
            text_threshold=0.6,  # ✅ Filtre texte peu confiant
            low_text=0.3         # ✅ Filtre boxes faibles
        )

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








    def _is_valid_name_token(self, text, is_nom=True):
        """
        Validation stricte d'un token nom/prénom
        """
        if not text or len(text.strip()) < 2:
            return False
        
        # Nettoyer d'abord les labels
        text = self._clean_label_noise(text)
        
        # Pas de chiffres
        if re.search(r'\d', text):
            return False
        
        # Nettoyer et vérifier longueur
        clean = re.sub(r'[^A-Za-zÀ-ÿ\s\-]', '', text).strip()
        if len(clean) < 2:
            return False
        
        # Mots interdits étendus
        FORBIDDEN = [
            'REPUBLIQUE', 'RÉPUBLIQUE', 'TOGOLAISE', 'TOGO',
            'MINISTERE', 'MINISTRE', 'CHARGE', 'SECURITE', 'SÉCURITÉ',
            'CARTE', 'IDENTITE', 'IDENTITÉ', 'NATIONALE', 'NATIONAL',
            'PASSEPORT', 'PERMIS', 'CONDUIRE', 'DOCUMENT',
            'EXPIRE', 'EXPIRATION', 'VALIDE', 'VALIDITE', 'VALIDITÉ',
            'NUMERO', 'NUMÉRO', 'SEXE', 'PROFESSION', 'SIGNATURE',
            'NE', 'NÉE', 'BIRTH', 'DATE', 'NATIONALITY',
            # ✅ AJOUTER : rejeter si contient juste le label
            'NOM', 'PRENOM', 'PRENOMS', 'NAME', 'SURNAME'
        ]
        
        text_upper = text.upper()
        
        # ✅ Rejeter si le texte EST un label
        if text_upper in FORBIDDEN:
            return False
        
        # Rejeter si contient un mot interdit
        if any(word in text_upper for word in FORBIDDEN):
            return False
        
        # Pour NOM : doit être majoritairement en majuscules
        if is_nom:
            alpha_chars = [c for c in clean if c.isalpha()]
            if alpha_chars:
                upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
                if upper_ratio < 0.6:
                    return False
        
        return True



    def _score_name_candidate(self, item, indexed_items, is_nom=True):
        """
        Score un candidat nom/prénom (0-10)
        """
        score = 0
        text = item['text']
        
        # Position verticale (0-3 points)
        if indexed_items:
            max_y = max(i['y'] for i in indexed_items)
            relative_y = item['y'] / max_y if max_y > 0 else 0
            
            if relative_y < 0.2:  # Top 20%
                score += 3
            elif relative_y < 0.35:  # Top 35%
                score += 2
            elif relative_y < 0.5:  # Top 50%
                score += 1
        
        # Confiance OCR (0-2 points)
        if item['confidence'] > 0.85:
            score += 2
        elif item['confidence'] > 0.7:
            score += 1
        
        # Longueur appropriée (0-2 points)
        text_len = len(text.strip())
        if 3 <= text_len <= 20:
            score += 2
        elif 2 <= text_len <= 25:
            score += 1
        
        # Format texte (0-3 points)
        if is_nom:
            # NOM en majuscules
            if text.isupper():
                score += 2
            # Pas de caractères spéciaux
            if text.replace('-', '').replace(' ', '').isalpha():
                score += 1
        else:
            # ✅ CORRIGÉ : PRENOM accepte MAJUSCULES ou Capitalisation
            if text.isupper():  # Tout en majuscules (ex: JEAN PAUL)
                score += 2
            elif text[0].isupper():  # Commence par majuscule (ex: Jean Paul)
                score += 2
            # Pas de caractères spéciaux
            if text.replace('-', '').replace(' ', '').isalpha():
                score += 1
        
        return score


    def _extract_value_after_label(self, text, label_patterns, is_nom=True):
        """
        Extrait la valeur après un label détecté
        """
        for label_pattern in label_patterns:
            # Patterns d'extraction
            patterns = [
                rf'{label_pattern}\s*[:]\s*([A-Za-zÀ-ÿ\s\-]+)',  # "NOM: Dupont"
                rf'{label_pattern}\s+([A-Za-zÀ-ÿ\s\-]+)',         # "NOM Dupont"
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
                    
                    # Limiter la longueur (prendre seulement les premiers mots)
                    words = candidate.split()
                    if len(words) > 3:
                        candidate = ' '.join(words[:3])
                    
                    if self._is_valid_name_token(candidate, is_nom=is_nom):
                        return candidate
        
        return None



    def extract_externe_fields(self, results, indexed):
        """
        Extraction optimisée du nom et prénom avec nettoyage des labels
        """
        nom = None
        prenom = None
        
        # Filtrer résultats avec confiance >= 0.5
        filtered_results = [r for r in results if r.get("confidence", 0) >= 0.5]
        if not filtered_results:
            filtered_results = results
        
        # ✅ Nettoyer chaque résultat des labels parasites
        cleaned_results = []
        for r in filtered_results:
            cleaned_text = self._clean_label_noise(r["text"])
            if cleaned_text:  # Garder seulement si non vide après nettoyage
                cleaned_results.append({
                    **r,
                    "text": cleaned_text,
                    "original_text": r["text"]  # Garder l'original pour debug
                })
        
        # Labels pour NOM et PRENOM
        NOM_LABELS = [r'N[OÔ]M\b', r'NAME\b', r'SURNAME\b']
        PRENOM_LABELS = [r'PR[EÉ]N[OÔ]MS?\b', r'FIRST\s*NAME', r'GIVEN\s*NAME']
        
        # Trier verticalement puis horizontalement
        sorted_results = sorted(cleaned_results, key=lambda r: (r["bbox"][0][1], r["bbox"][0][0]))
        
        # Texte complet
        full_text = " ".join([r["text"] for r in sorted_results])
        
        print(f"🔍 Texte OCR nettoyé: {full_text[:200]}...")
        print(f"📊 {len(sorted_results)} résultats après nettoyage")
        
        # ========================================
        # STRATÉGIE 1 : Détecter structure "NOM PRENOM(S)"
        # ========================================
        # Pattern : MAJUSCULES suivi de mots capitalisés
        #pattern_nom_prenoms = r'([A-ZÀ-Ÿ\-]+)\s+([A-Za-zÀ-ÿ\s\-]+)'
        pattern_nom_prenoms = r'([A-ZÀ-Ÿ\-]+)\s+([A-ZÀ-ÿ\s\-]+)'  # Prénom peut être MAJUSCULE ou Capitalisé

        for r in sorted_results[:5]:  # Chercher dans les 5 premières lignes
            match = re.match(pattern_nom_prenoms, r["text"].strip())
            if match and not nom and not prenom:
                candidate_nom = match.group(1).strip()
                candidate_prenoms = match.group(2).strip()
                
                if (self._is_valid_name_token(candidate_nom, is_nom=True) and
                    self._is_valid_name_token(candidate_prenoms, is_nom=False)):
                    nom = candidate_nom
                    prenom = candidate_prenoms
                    print(f"✅ Trouvé via pattern : Nom={nom}, Prénoms={prenom}")
                    break
        
        # ========================================
        # STRATÉGIE 2 : Recherche par position spatiale
        # ========================================
        if not nom or not prenom:
            top_items = indexed.get('top_region', indexed.get('items', []))
            
            # Nettoyer les items aussi
            top_items_cleaned = []
            for item in top_items:
                cleaned = self._clean_label_noise(item['text'])
                if cleaned and self._is_valid_name_token(cleaned):
                    top_items_cleaned.append({
                        **item,
                        'text': cleaned
                    })
            
            # Trier par position verticale puis score
            candidates = []
            for item in top_items_cleaned:
                score = self._score_name_candidate(item, indexed['items'])
                candidates.append({
                    'text': item['text'],
                    'score': score,
                    'is_upper': item['text'].isupper(),
                    'y': item['y']
                })
            
            candidates.sort(key=lambda x: (x['y'], -x['score']))
            
            # Premier candidat en majuscules = NOM
            if not nom:
                for cand in candidates:
                    if cand['is_upper']:
                        nom = cand['text'].upper()
                        print(f"✅ Nom (spatial): {nom}")
                        break
            
            # ✅ CORRIGÉ : Candidat suivant (majuscules ou capitalisé) = PRENOM(S)
            if not prenom:
                for cand in candidates:
                    if cand['text'] != nom:  # Juste différent du nom
                        print(f"🔍 Test prénom spatial: '{cand['text']}'")
                        if self._is_valid_name_token(cand['text'], is_nom=False):
                            prenom = cand['text']
                            print(f"✅ Prénom(s) (spatial): {prenom}")
                            break
        
        # ========================================
        # STRATÉGIE 3 : Ligne par ligne (fallback)
        # ========================================
        if not nom or not prenom:
            for i, r in enumerate(sorted_results):
                txt = r["text"].strip()
                
                # ✅ CORRIGÉ : Chercher NOM d'abord
                if not nom and txt.isupper() and len(txt) >= 3:
                    if self._is_valid_name_token(txt, is_nom=True):
                        nom = txt
                        print(f"✅ Nom (ligne {i}): {nom}")
                
                # ✅ NOUVEAU : Si on a le NOM, chercher PRENOM juste après
                if nom and not prenom:
                    # Chercher dans les 3 lignes suivantes
                    for j in range(i + 1, min(i + 4, len(sorted_results))):
                        next_txt = sorted_results[j]["text"].strip()
                        
                        # ✅ Le prénom peut être en MAJUSCULES ou Capitalisé
                        if len(next_txt) >= 3 and next_txt != nom:
                            print(f"🔍 Test prénom candidat (ligne {j}): '{next_txt}'")
                            
                            if self._is_valid_name_token(next_txt, is_nom=False):
                                prenom = next_txt
                                print(f"✅ Prénom(s) (ligne {j}): {prenom}")
                                break
                    
                    # Si prénom trouvé, sortir de la boucle principale
                    if prenom:
                        break
        
        # ========================================
        # Normalisation finale
        # ========================================
        if nom:
            nom = ' '.join(nom.split()).upper()
            # Validation finale
            if not self._is_valid_name_token(nom, is_nom=True):
                print(f"⚠️ Nom rejeté après validation: {nom}")
                nom = None
        
        if prenom:
            prenom = ' '.join(prenom.split())
            # Capitaliser chaque mot
            #prenom = ' '.join(word.capitalize() for word in prenom.split())
            if not self._is_valid_name_token(prenom, is_nom=False):
                print(f"⚠️ Prénom rejeté après validation: {prenom}")
                prenom = None
        
        print(f"📝 RÉSULTAT FINAL - Nom: {nom}, Prénom(s): {prenom}")
        
        return {
            "nom": nom,
            "prenom": prenom
        }
        

    
    def _clean_label_noise(self, text):
        """
        Supprime les labels OCR parasites (NOM:, PRÉNOM:, etc.)
        """
        # Labels à supprimer
        labels_to_remove = [
            r'\bN[OÔ]M\s*:?\s*',
            r'\bPR[EÉ]N[OÔ]MS?\s*:?\s*',
            r'\bNAME\s*:?\s*',
            r'\bSURNAME\s*:?\s*',
            r'\bFIRST\s*NAME\s*:?\s*',
            r'\bLAST\s*NAME\s*:?\s*',
            r'\bGIVEN\s*NAME\s*:?\s*',
        ]
        
        cleaned = text
        for pattern in labels_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Nettoyer espaces multiples
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned

    def index_ocr_results(self, results):
        """
        Indexation spatiale OCR améliorée :
        - normalise le texte
        - calcule centre (x, y)
        - groupe par lignes
        - identifie la zone supérieure (prioritaire pour nom/prénom)
        """
        indexed = []
        
        if not results:
            return {"items": [], "lines": [], "top_region": []}

        for r in results:
            bbox = r["bbox"]
            x_vals = [p[0] for p in bbox]
            y_vals = [p[1] for p in bbox]

            x_center = sum(x_vals) / len(x_vals)
            y_center = sum(y_vals) / len(y_vals)

            indexed.append({
                "text": r["text"],
                "text_norm": clean_text_for_matching(r["text"]),
                "confidence": r["confidence"],
                "bbox": bbox,
                "x": x_center,
                "y": y_center
            })

        # Trier top → bottom puis left → right
        indexed.sort(key=lambda i: (i["y"], i["x"]))

        # Grouper par lignes (tolérance verticale)
        lines = []
        line_tol = 18  # pixels

        for item in indexed:
            placed = False
            for line in lines:
                if abs(line[0]["y"] - item["y"]) < line_tol:
                    line.append(item)
                    placed = True
                    break
            if not placed:
                lines.append([item])

        # Trier chaque ligne gauche → droite
        for line in lines:
            line.sort(key=lambda i: i["x"])

        # ✅ NOUVEAU : Identifier la zone supérieure (35% du haut)
        if indexed:
            max_y = max(item['y'] for item in indexed)
            threshold_y = max_y * 0.35
            top_region = [item for item in indexed if item['y'] <= threshold_y]
        else:
            top_region = []

        return {
            "items": indexed,
            "lines": lines,
            "top_region": top_region  # ✅ Zone prioritaire
        }