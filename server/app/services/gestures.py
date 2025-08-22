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
            return GestureEvent(gesture="none")

        # Usar la primera mano detectada
        landmarks = result.multi_hand_landmarks[0].landmark

        def is_finger_up(tip_idx: int, pip_idx: int) -> bool:
            # Coordenadas normalizadas [0..1]; menor y => más arriba en la imagen
            return landmarks[tip_idx].y < landmarks[pip_idx].y

        index_up = is_finger_up(8, 6)
        middle_up = is_finger_up(12, 10)

        if index_up and middle_up:
            return GestureEvent(gesture="next")
        if index_up and not middle_up:
            return GestureEvent(gesture="prev")

        return GestureEvent(gesture="none")
