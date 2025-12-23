
import cv2
import pickle
import numpy as np
from deepface import DeepFace
from deepface.modules.verification import find_distance
from PIL import Image
import io
import os

# Configuration
MODEL_NAME = "Facenet512"
METRIC = "euclidean_l2"
THRESHOLD = 0.78


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBS_PATH = os.path.join(BASE_DIR, "..", "public", "embeddings", "embs_facenet512.pkl")
EMBS_PATH = os.path.abspath(EMBS_PATH)


EMBEDDINGS = {}

def load_embeddings():
    """Charge les embeddings depuis le fichier pickle."""
    global EMBEDDINGS
    if not EMBEDDINGS:
        try:
            with open(EMBS_PATH, "rb") as file:
                EMBEDDINGS = pickle.load(file)
                print(f"[Service] Embeddings chargés : {len(EMBEDDINGS)} visages connus.")
                return True
        except FileNotFoundError:
            print("[Service] Erreur : Fichier d'embeddings introuvable.")
            EMBEDDINGS = {}
            return False
        except Exception as e:
            print(f"[Service] Erreur lors du chargement des embeddings: {str(e)}")
            EMBEDDINGS = {}
            return False

def clahe(image):
    """Applique l'égalisation d'histogramme CLAHE."""
    clahe_obj = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe_obj.apply(image)

def recognize_face(image_data):
    """
    Traite l'image fournie (bytes ou stream) et renvoie la prédiction.
    
    Args:
        image_data: Données brutes de l'image (bytes)
    
    Returns:
        tuple: (resultat_dict, code_statut)
    """
    if not EMBEDDINGS:
        return {"error": "Base de données d'embeddings non chargée", "status": "error"}, 503

    try:
        # 1. Convertir l'image en format OpenCV
        img = Image.open(io.BytesIO(image_data)).convert('RGB')
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # 2. Détection de visages
        results = DeepFace.extract_faces(
            frame, detector_backend="yolov8", enforce_detection=False
        )

        if not results or len(results) == 0:
            return {
                "prediction": "Inconnu", 
                "message": "Aucun visage détecté", 
                "distance": None,
                "status": "success"
            }, 200

        # Traiter le premier visage détecté
        result = results[0]
        facial_area = result.get("facial_area", {})
        
        if not facial_area:
            return {
                "prediction": "Inconnu", 
                "message": "Visage détecté mais zone faciale non trouvée", 
                "distance": None,
                "status": "success"
            }, 200

        x, y, w, h = facial_area["x"], facial_area["y"], facial_area["w"], facial_area["h"]

        # 3. Prétraitement de l'image (cropping, CLAHE, resize)
        cropped_face = frame[y:y + h, x:x + w]
        cropped_resized = cv2.resize(cropped_face, (224, 224))
        gray_face = cv2.cvtColor(cropped_resized, cv2.COLOR_BGR2GRAY)
        clahe_face = clahe(gray_face)
        rgb_face = cv2.cvtColor(clahe_face, cv2.COLOR_GRAY2RGB)

        # 4. Calcul de l'embedding
        emb_result = DeepFace.represent(
            rgb_face,
            model_name=MODEL_NAME,
            enforce_detection=False,
            detector_backend="skip",
        )
        
        if not emb_result:
            return {"error": "Impossible de calculer l'embedding", "status": "error"}, 500
            
        emb = emb_result[0]["embedding"]

        # 5. Comparaison avec la base de données
        min_dist = float("inf")
        match_name = "Inconnu"
        
        for name, emb2 in EMBEDDINGS.items():
            dst = find_distance(emb, emb2, METRIC)
            if dst < min_dist:
                min_dist = dst
                match_name = name
        
        # 6. Appliquer le seuil
        if min_dist > THRESHOLD:
            match_name = "Inconnu"

        return {
            "prediction": match_name,
            "distance": round(min_dist, 4),
            "threshold": THRESHOLD,
            "metric": METRIC,
            "status": "success",
            "faces_detected": len(results)
        }, 200

    except Exception as e:
        return {"error": f"Erreur lors du traitement: {str(e)}", "status": "error"}, 500

# Charger les embeddings au démarrage du module
load_embeddings()
