import cv2
import socket
import struct
import pickle
import time

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 5000))  # 포트 5000에서 수신
    server_socket.listen(1)
    print("클라이언트 연결 대기 중...")

    conn, addr = server_socket.accept()
    print(f"클라이언트 {addr} 연결됨.")

    cap = cv2.VideoCapture(0)  # 카메라 장치 열기

    while True:
        ret, frame = cap.read()
        if not ret:
            break
       
        # 이미지 직렬화
        data = pickle.dumps(frame)
        # 데이터 전송
        conn.sendall(struct.pack("L", len(data)) + data)

    cap.release()
    conn.close()
    server_socket.close()

if __name__ == "__main__":
    start_server()