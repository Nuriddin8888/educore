from insightface.app import FaceAnalysis

face_app = None


def get_face_app():
    global face_app

    if face_app is None:

        face_app = FaceAnalysis(
            name="buffalo_sc",
            providers=["CPUExecutionProvider"]
        )

        face_app.prepare(
            ctx_id=0,
            det_size=(320, 320)
        )

    return face_app