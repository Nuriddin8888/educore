from insightface.app import FaceAnalysis

face_app = FaceAnalysis(
    name="buffalo_l"
)

face_app.prepare(
    ctx_id=0,
    det_size=(640, 640)
)