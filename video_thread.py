from PySide6.QtCore import Qt, QThread, Signal, Slot, QFile
import torch
import easyocr
import string
import json
import cv2
import sys


class VideoThread(QThread):
    change_pixmap_signal = Signal(dict)

    def get_anpr_model(self):
        model = torch.hub.load('./yolov5',
                               'custom',
                               path='./model/best-anpr.pt',
                               source='local',
                               force_reload=True)

        model.conf = 0.5
        cpu_or_cuda = "mps" if torch.backends.mps.is_available() else 'cpu'
        print(f'Device chosen: {cpu_or_cuda}')
        device = torch.device(cpu_or_cuda)
        model = model.to(device)
        print('Model is returning....\n')
        return model

    def __init__(self, device):
        super().__init__()
        self.device = device
        self._run_flag = True
        self.model = self.get_anpr_model()
        self.ocr = easyocr.Reader(['en'], gpu=False)
        self.allowlist = string.digits + string.ascii_letters
        self.text_font = cv2.FONT_HERSHEY_PLAIN
        self.text_font_scale = 2
        self.color = (0, 0, 255)

    def get_bbox_content(self, img):
        result = self.ocr.readtext(
            img,
            allowlist=self.allowlist
        )
        plate_num = self.get_Text(result)
        return plate_num

    def get_Text(self, result):
        try:
            txts = [line[1] for line in result if len(line[1]) < 7]
            if len(txts) > 4:
                txts = txts[:5]
            return ' '.join(txts)
        except Exception as e:
            print(e)
            return ""

    def get_bbox(self, image):
        results = self.model(image)
        detect_res = results.pandas().xyxy[0].to_json(
            orient="records")  # JSON img1 predictions
        detect_res = json.loads(detect_res)

        plates = []

        for item in detect_res:
            x1 = int(item['xmin'])
            x2 = int(item['xmax'])
            y1 = int(item['ymin'])
            y2 = int(item['ymax'])

            text_origin = (x1, y1-10)
            cropped = image[y1:y2, x1:x2]
            # plates.append(cropped)

            try:
                plate = self.get_bbox_content(cropped)
                plates.append(plate)
            except Exception as e:
                print(e)
                plate = str(e)

            item['plate_number'] = plate

            image = cv2.rectangle(
                image, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=10)

            cv2.putText(
                image,
                text=plate,
                org=text_origin,
                fontFace=self.text_font,
                fontScale=5,
                color=self.color,
                thickness=4
            )
        return {'image': image, 'plates': plates}

    def run(self):
        # capture from web cam
        device_ = int(self.device) if str(
            self.device).isnumeric() else self.device
        cap = cv2.VideoCapture(device_)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                result = self.get_bbox(cv_img)
                self.change_pixmap_signal.emit(result)
        # shut down capture system
        cap.release()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()
