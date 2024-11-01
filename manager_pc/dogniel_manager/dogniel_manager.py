import sys
import socket
import cv2
import pickle
import struct
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QPushButton, QLabel, QStackedWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QThread, pyqtSignal
import mysql.connector

class VideoStreamThread(QThread):
    update_frame = pyqtSignal(QImage)

    def __init__(self, server_ip):
        super().__init__()
        self.server_ip = server_ip
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        self.client_socket.connect((self.server_ip, 4000))  # 서버 IP와 포트
        while True:
            try:
                data_size_bytes = self.client_socket.recv(struct.calcsize('L'))
                if not data_size_bytes:
                    print("클라이언트와의 연결이 끊어졌습니다.")
                    break
                data_size = struct.unpack('L', data_size_bytes)[0]
                data = b''
                while len(data) < data_size:
                    packet = self.client_socket.recv(data_size - len(data))
                    if not packet:
                        print("클라이언트와의 연결이 끊어졌습니다.")
                        break
                    data += packet
                frame = pickle.loads(data)

                # OpenCV로 이미지를 QLabel에 표시할 수 있는 형식으로 변환
                frame = cv2.resize(frame, dsize=(640, 640))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # BGR에서 RGB로 변환
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.update_frame.emit(q_img)

            except Exception as e:
                print(f"오류 발생: {e}")
                break
        self.client_socket.close()

class VideoStreamThread_cctv(QThread):
    update_frame_cctv = pyqtSignal(QImage)

    def __init__(self, server_cctv_ip):
        super().__init__()
        self.server_cctv_ip = server_cctv_ip
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        self.client_socket.connect((self.server_cctv_ip, 5000))  # 서버 IP와 포트
        while True:
            try:
                data_size_bytes = self.client_socket.recv(struct.calcsize('L'))
                if not data_size_bytes:
                    print("클라이언트와의 연결이 끊어졌습니다.")
                    break
                data_size = struct.unpack('L', data_size_bytes)[0]
                data = b''
                while len(data) < data_size:
                    packet = self.client_socket.recv(data_size - len(data))
                    if not packet:
                        print("클라이언트와의 연결이 끊어졌습니다.")
                        break
                    data += packet
                frame = pickle.loads(data)

                # OpenCV로 이미지를 QLabel에 표시할 수 있는 형식으로 변환
                frame = cv2.resize(frame, dsize=(640, 640))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # BGR에서 RGB로 변환
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.update_frame_cctv.emit(q_img)

            except Exception as e:
                print(f"오류 발생: {e}")
                break
        self.client_socket.close()

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('/home/addinedu/ros-repo-demo/manager_pc/dogniel_manager/dogniel_manager.ui', self)

        self.stacked_widget = self.findChild(QStackedWidget, 'stackedWidget')
        self.stacked_widget.hide()

        self.c_Button.clicked.connect(self.toggle_options1)
        self.r_Button.clicked.connect(self.toggle_options2)

        self.hide_sub_buttons(self.verticalLayoutWidget)
        self.hide_sub_buttons(self.verticalLayoutWidget_2)

        self.c1_Button.clicked.connect(lambda: self.go_to_page(0))
        self.c2_Button.clicked.connect(lambda: self.go_to_page(1))
        self.c3_Button.clicked.connect(lambda: self.go_to_page(2))

        self.r1_Button.clicked.connect(lambda: self.go_to_page(3))
        self.r2_Button.clicked.connect(lambda: self.go_to_page(4))

        self.p1_check_Button.clicked.connect(self.customer_check)

        self.p1_listWidget.itemClicked.connect(self.on_list_item_click)

        # 비디오 스트리밍 스레드 시작
        #self.server_ip = '192.168.0.4'  # Raspberry Pi의 IP 주소
        #self.video_thread = VideoStreamThread(self.server_ip)
        #self.video_thread.update_frame.connect(self.update_video_frame)
        #self.video_thread.start()

        # 비디오 스트리밍 스레드 시작
        self.server_cctv_ip = 'localhost'  # cctv의 IP주소
        self.video_thread_cctv = VideoStreamThread_cctv(self.server_cctv_ip)
        self.video_thread_cctv.update_frame_cctv.connect(self.update_video_frame_cctv)
        self.video_thread_cctv.start()

    def update_video_frame_cctv(self, frame):
        """QLabel에 비디오 프레임을 업데이트하는 함수."""
        self.p4_cctv_Label.setPixmap(QPixmap.fromImage(frame))

    def update_video_frame(self, frame):
        """QLabel에 비디오 프레임을 업데이트하는 함수."""
        self.p5_minibot_cam_2_Label.setPixmap(QPixmap.fromImage(frame))

    def connect_to_db(self):
        try:
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='0',
                database='dogniel_database'
            )
            return connection
        except mysql.connector.Error as e:
            print(f"DB 연결 실패: {e}")
            return None

    def hide_sub_buttons(self, widget):
        if widget is not None:
            widget.hide()
            for button in widget.findChildren(QPushButton):
                button.hide()

    def toggle_options1(self):
        if self.verticalLayoutWidget.isVisible():
            self.hide_sub_buttons(self.verticalLayoutWidget)
        else:
            self.verticalLayoutWidget.show()
            for button in self.verticalLayoutWidget.findChildren(QPushButton):
                button.show()
            self.stacked_widget.show()

    def toggle_options2(self):
        if self.verticalLayoutWidget_2.isVisible():
            self.hide_sub_buttons(self.verticalLayoutWidget_2)
        else:
            self.verticalLayoutWidget_2.show()
            for button in self.verticalLayoutWidget_2.findChildren(QPushButton):
                button.show()
            self.stacked_widget.show()

    def go_to_page(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def customer_check(self):
        name_text = self.name.text()
        phone_num = str(self.phone_num.text())
        self.p1_name.clear()
        self.p1_phone_num.clear()

        if name_text and phone_num:
            connection = self.connect_to_db()
            if connection:
                cursor = connection.cursor()
                query = "SELECT name FROM customer_information WHERE name = %s AND phone_number LIKE %s"
                cursor.execute(query, (name_text, f'%{phone_num}'))

                results = cursor.fetchall()
                cursor.close()
                connection.close()

                self.listWidget.clear()  # 이전 검색 결과 지우기
                if results:
                    for row in results:
                        self.listWidget.addItem(row[0])  # 이름을 리스트에 추가
                else:
                    QMessageBox.information(self, '결과', '고객을 찾을 수 없습니다.')
        else:
            QMessageBox.warning(self, '경고', '이름과 전화번호 뒷자리를 모두 입력해주세요.')

    def on_list_item_click(self, item):
        name = item.text()
        response = QMessageBox.question(self, '체크인', f'{name}을 체크인 하시겠습니까?',
                                         QMessageBox.Yes | QMessageBox.No)

        if response == QMessageBox.Yes:
            print(f'{name} 체크인 완료!')
        else:
            print(f'{name} 체크인 취소.')

    def register(self):
        # 입력값 가져오기
        name = self.p2_name.text()
        gender = self.p2_gender.text()
        birth_date = self.p2_birth_date.text()
        phone_number = self.p2_phone_num.text()
        dog_name = self.p2_dog_name.text()
        dog_breed = self.p2_dog_breed.text()
        dog_gender = self.p2_dog_gender.text()
        dog_birth_year = self.p2_dog_birth_year.text()
        dog_neutered = self.p2_dog_neutered.text()
        dog_health_issue = self.p2_dog_health_issue.text()
        dog_vaccination_status = self.p2_dog_vaccination_status.text()
        dog_remarks = self.p2_dog_remarks.text()

        # SQL 쿼리
        try:
            # 고객 정보 삽입
            insert_customer_query = """
            INSERT INTO customer_information (name, gender, birth_date, phone_number)
            VALUES (%s, %s, %s, %s)
            """
            customer_data = (name, gender, birth_date, phone_number)
            self.cursor.execute(insert_customer_query, customer_data)
            customer_id = self.cursor.lastrowid  # 마지막 삽입된 고객 ID 가져오기

            # 반려견 정보 삽입
            insert_dog_query = """
            INSERT INTO dog_information (id, dog_name, dog_breed, dog_gender, dog_birth_year,
                                         dog_neutered, dog_health_issue, dog_vaccination_status, dog_remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            dog_data = (customer_id, dog_name, dog_breed, dog_gender, dog_birth_year,
                        dog_neutered, dog_health_issue, dog_vaccination_status, dog_remarks)
            self.cursor.execute(insert_dog_query, dog_data)

            # 커밋
            self.db.commit()

            QMessageBox.information(self, "Success", "등록 완료!")
            self.clear_fields()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"등록 실패: {e}")
            self.db.rollback()

    def clear_fields(self):
        # 입력 필드 초기화
        self.p2_name.clear()
        self.p2_birth_date.clear()
        self.p2_phone_num.clear()
        self.p2_dog_name.clear()
        self.p2_dog_breed.clear()
        self.p2_dog_gender.clear()
        self.p2_dog_birth_year.clear()
        self.p2_dog_neutered.clear()
        self.p2_dog_health_issue.clear()
        self.p2_dog_vaccination_status.clear()
        self.p2_dog_remarks.clear()
        self.p2_gender.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    my_app = MyApp()
    my_app.show()
    sys.exit(app.exec_())
