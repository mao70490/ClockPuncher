import io, os
import cv2
import numpy as np
from PIL import Image, ImageEnhance
from tensorflow.keras.models import load_model

class CaptchaSolver:
    def __init__(self, model_path, dataset_path):
        self.model = load_model(model_path)
        self.classes = sorted(os.listdir(dataset_path))
        # 固定紅框參數
        self.x0, self.y0 = 9, 9
        self.char_w, self.char_h = 16, 20
        self.num_chars = 5
        self.margin = 1

    def solve(self, captcha_png: bytes) -> str:
        image = Image.open(io.BytesIO(captcha_png))
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # 灰階 + 去雜訊 + 增強
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        pil_img = Image.fromarray(blur)
        enhanced = ImageEnhance.Contrast(pil_img).enhance(3.0)
        gray_enhanced = np.array(enhanced)

        # 二值化 + 去雜點
        binary = cv2.adaptiveThreshold(
            gray_enhanced, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        kernel = np.ones((2, 2), np.uint8)
        clean = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        # 預測每個字
        predicted_text = ""
        for j in range(self.num_chars):
            char_img = clean[
                self.y0 - self.margin:self.y0 - self.margin + self.char_h + 2 * self.margin,
                self.x0 + j * self.char_w - self.margin:self.x0 + (j + 1) * self.char_w + 2 * self.margin
            ]
            char_img = char_img / 255.0
            char_img = np.expand_dims(char_img, axis=-1)  
            char_img = np.expand_dims(char_img, axis=0)   

            pred = self.model.predict(char_img, verbose=0)
            class_idx = np.argmax(pred)
            predicted_text += self.classes[class_idx]

        return predicted_text
