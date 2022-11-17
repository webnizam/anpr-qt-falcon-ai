# This Python file uses the following encoding: utf-8
import os
from pathlib import Path
import sys

from PySide6 import QtGui
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QListWidgetItem, QVBoxLayout
from PySide6.QtCore import Qt, QThread, Signal, Slot, QFile
from PySide6.QtUiTools import QUiLoader
import cv2
import numpy as np

from db import DatabaseManager
from video_thread import VideoThread


class ImageQWidget(QWidget):
    def __init__(self, label, image, parent=None):
        super(ImageQWidget, self).__init__(parent)

        img_label = QLabel(label)
        img_label.setPixmap(image)

        img_label.adjustSize()

        layout = QVBoxLayout()
        layout.addStretch(1)
        layout.addWidget(img_label)
        self.setLayout(layout)


class Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = self.load_ui()

        self.disply_width = 640
        self.display_height = 360
        self.current_image = None

        self.db = DatabaseManager()

        self.load_all_records()

        self.thread = VideoThread(0)
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

        self.ui.btn_add_image.clicked.connect(self.add_image)
        self.ui.btn_clear_log.clicked.connect(self.clear_log)
        self.ui.btn_add_plate.clicked.connect(self.add_plate)
        self.ui.btn_remove_plate.clicked.connect(self.remove_plate)
        self.ui.btn_clear_list.clicked.connect(self.clear_list)
        self.ui.btn_apply.clicked.connect(self.change_device)

    def change_device(self):
        device = self.ui.le_device.text()
        print('change device to:', device)
        if device:
            try:
                self.thread.stop()
                self.thread = VideoThread(device=device)
                self.thread.change_pixmap_signal.connect(self.update_image)
                self.thread.start()
            except Exception as e:
                print(e)

    def add_plate(self):
        record = self.ui.le_input_field.text()
        if record:
            self.db.add_record(record)
            self.ui.le_input_field.setText('')
            self.load_all_records()

    def remove_plate(self):
        record = self.ui.lv_authorized_number_plates.currentItem().text()
        self.db.remove_record(record)
        self.load_all_records()

    def clear_log(self):
        self.ui.lv_recognized_plates.clear()

    def clear_list(self):
        pass

    def load_all_records(self):
        records = self.db.get_all_records()
        self.ui.lv_authorized_number_plates.clear()
        for record in records:
            self.ui.lv_authorized_number_plates.addItem(
                str(record['plate_number']))

    def add_image(self):
        if self.current_image:
            qlitem = QListWidgetItem(self.ui.lv_recognized_plates)
            item = ImageQWidget('Image', self.current_image)
            qlitem.setSizeHint(item.sizeHint())
            self.ui.lv_recognized_plates.addItem(qlitem)
            self.ui.lv_recognized_plates.setItemWidget(qlitem, item)

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    @Slot(np.ndarray)
    def update_image(self, result):
        """Updates the image_label with a new opencv image"""

        cv_img = result['image']
        plates = result['plates']

        if plates:
            recognized = False
            for plate in plates:
                recognized = self.db.check_if_exists(plate)

            qlitem = QListWidgetItem(self.ui.lv_recognized_plates)
            if recognized:
                qlitem.setBackground(QColor('green'))
            else:
                qlitem.setBackground(QColor('red'))
            qlitem.setText(' '.join(plates))
            self.ui.lv_recognized_plates.addItem(qlitem)
            self.ui.lv_recognized_plates.scrollToBottom()

        qt_img = self.convert_cv_qt(cv_img)
        self.current_image = qt_img
        self.ui.image_view.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(
            rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(
            self.disply_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def load_ui(self):
        loader = QUiLoader()
        path = Path(__file__).resolve().parent / "main.ui"
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        window = loader.load(ui_file, self)
        ui_file.close()
        return window


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.setFixedSize(960, 550)
    widget.show()
    sys.exit(app.exec())
