import cv2
import numpy as np

from app.core.face import get_face_app


def extract_embedding(image_path: str):

    img = cv2.imread(image_path)

    if img is None:
        return None

    face_app = get_face_app()
    faces = face_app.get(img)

    if len(faces) == 0:
        return None

    return faces[0].embedding.tolist()


def cosine_similarity(vec1, vec2):

    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    similarity = np.dot(
        vec1,
        vec2
    ) / (
        np.linalg.norm(vec1)
        * np.linalg.norm(vec2)
    )

    return float(similarity)