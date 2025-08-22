from dataclasses import dataclass
from typing import Optional
import cv2
import mediapipe as mp


@dataclass
class GestureEvent:
    gesture: str  # "next" | "prev" | "none"


class HandGestureDetector:
    def __init__(self) -> None:
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(model_complexity=0, min_detection_confidence=0.5, min_tracking_confidence=0.5)

    def __del__(self):
        try:
            self.hands.close()
        except Exception:
            pass

    def infer_frame(self, frame_bgr) -> Optional[GestureEvent]:
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result = self.hands.process(frame_rgb)
        if not result.multi_hand_landmarks:
            return None
        # Heurística simple: dirección del pulgar vs. índice para inferir gesto.
        # Nota: Esto es un placeholder; el frontend hará la detección en el navegador.
        return GestureEvent(gesture="none")
