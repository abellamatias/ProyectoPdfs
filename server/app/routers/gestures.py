from fastapi import APIRouter, UploadFile, File, HTTPException
import numpy as np
import cv2

from ..services.gestures import HandGestureDetector
from ..schemas import GestureInferResponse


router = APIRouter()

_detector = HandGestureDetector()


@router.post("/infer", response_model=GestureInferResponse)
async def infer_gesture(file: UploadFile = File(...)):
    try:
        # Espera una imagen (jpeg/png). Leemos bytes y decodificamos a BGR.
        content = await file.read()
        np_arr = np.frombuffer(content, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise HTTPException(status_code=400, detail="Imagen inválida")
        evt = _detector.infer_frame(frame)
        gesture = evt.gesture if evt else "none"
        return {"gesture": gesture}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error procesando imagen")


