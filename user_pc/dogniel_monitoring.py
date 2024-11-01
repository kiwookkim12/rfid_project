import sys
import cv2
import socket
import pickle
import struct
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QMainWindow, QWidget
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt, QThread
import time

class VideoReceiver(QThread):
    def __init__(self, socket, label):
        super().__init__()
        self.socket = socket
        self.label = label

    def run(self):
        while True:
            data = b""
            while len(data) < struct.calcsize("L"):
                data += self.socket.recv(4096)
            packed_size = data[:struct.calcsize("L")]
            data = data[struct.calcsize("L"):]

            frame_size = struct.unpack("L", packed_size)[0]
            while len(data) < frame_size:
                data += self.socket.recv(4096)
            frame_data = data[:frame_size]
            data = data[frame_size:]

            frame = pickle.loads(frame_data)
            self.display_frame(frame)

    def display_frame(self, frame):
        # QLabel 크기 가져오기
        label_width = self.label.width()
        label_height = self.label.height()

        # 프레임 리사이즈
        resized_frame = cv2.resize(frame, (label_width, label_height))
        resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

        # QImage로 변환
        q_img = QImage(resized_frame.data, label_width, label_height, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.label.setPixmap(pixmap)

class VideoCapture(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("coordinate.py.ui", self)

        self.setWindowTitle("Webcam Capture")
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(('localhost', 5000))

        self.image_label = self.findChild(QLabel, "label")
        self.image_label.setFixedSize(1000, 600)

        self.clicked_point = None
        self.coordinates_label = QLabel("Clicked Coordinates: ( , )", self)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.coordinates_label)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.recv_thread = VideoReceiver(self.client_socket, self.image_label)
        self.recv_thread.start()

    def mousePressEvent(self, event):
        # QLabel 기준으로 클릭 이벤트 처리
        if event.button() == Qt.LeftButton:
            if self.image_label.geometry().contains(event.pos()):
                self.clicked_point = event.pos() - self.image_label.pos()  # QLabel의 위치 기준으로 클릭 좌표 저장
                coord_text = f"Clicked Coordinates: ({self.clicked_point.x()}, {self.clicked_point.y()})"
                self.coordinates_label.setText(coord_text)
                self.send_coordinates()
                self.image_label.update()  # QLabel을 업데이트하여 다시 그리기

    def send_coordinates(self):
        if self.clicked_point:
            coordinates = (self.clicked_point.x(), self.clicked_point.y())
            data = pickle.dumps(coordinates)
            self.client_socket.sendall(data)

    def paintEvent(self, event):
        # QLabel에 빨간 원 그리기
        if self.clicked_point:
            painter = QPainter(self.image_label.pixmap())
            painter.setPen(QColor(255, 0, 0))  # 빨간색
            painter.setBrush(QColor(255, 0, 0))
            adjusted_x = self.clicked_point.x()
            adjusted_y = self.clicked_point.y()
            painter.drawEllipse(adjusted_x - 8, adjusted_y - 8, 10, 10)  # 점의 크기
            painter.end()
            self.image_label.update()  # QLabel 업데이트

    def closeEvent(self, event):
        self.client_socket.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VideoCapture()
    window.show()
    sys.exit(app.exec_())

