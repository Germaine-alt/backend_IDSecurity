from deepface import DeepFace
import os
from tqdm import tqdm
import cv2
import matplotlib.pyplot as plt


def crop(input_dir, output_dir, detector_backend="yolov8"):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    for img_file in tqdm(os.listdir(input_dir)):
        img_path = os.path.join(input_dir, img_file)
        img_name = img_file.split(".")[0]

        try:
            faces = DeepFace.extract_faces(
                img_path,
                detector_backend=detector_backend,
                enforce_detection=False,   # IMPORTANT
                grayscale=True
            )

            if len(faces) == 0:
                print(f"⚠️ Aucun visage détecté dans : {img_file}")
                continue

            face = faces[0]["face"]

            # Vérifier les valeurs de pixels
            print(f"Max pixel value in extracted face: {face.max()}")
            print(f"Min pixel value in extracted face: {face.min()}")

            # Normalisation si nécessaire
            if face.dtype != 'uint8':
                face = cv2.normalize(face, None, 0, 255, cv2.NORM_MINMAX).astype('uint8')

            # Convertir en RGB (si grayscale)
            if len(face.shape) == 2:  # image grayscale
                face = cv2.cvtColor(face, cv2.COLOR_GRAY2RGB)

            # Redimensionner
            face = cv2.resize(face, (224, 224))

            # Sauvegarde
            plt.imsave(f"{output_dir}/{img_name}.jpg", face)

            print(f"✔️ Visage sauvegardé : {output_dir}/{img_name}.jpg")

        except Exception as e:
            print(f"❌ Erreur avec {img_file} : {e}")
            continue


crop("../public/uploads", "../public/cropped_faces")
