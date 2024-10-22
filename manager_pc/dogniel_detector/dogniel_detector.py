import socket
import cv2
import pickle
import struct

from ultralytics import YOLO

# YOLO 모델 로드
#model = YOLO("best.pt") ---------------------------------------------------pt파일 보유 시 주석 제거

def receive_video(server_ip):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, 5000))  # 서버 IP와 포트

    while True:
        try:
            data_size_bytes = client_socket.recv(struct.calcsize('L'))
            if not data_size_bytes:
                print("클라이언트와의 연결이 끊어졌습니다.")
                break
            data_size = struct.unpack('L', data_size_bytes)[0]
            data = b''
            while len(data) < data_size:
                packet = client_socket.recv(data_size - len(data))
                if not packet:
                    print("클라이언트와의 연결이 끊어졌습니다.")
                    break
                data += packet
            frame = pickle.loads(data)
            frame = cv2.resize(frame, dsize=(640,640))
            #frame = model(frame) ---------------------------------------pt파일 보유 시 주석 제거
        except Exception as e:
                print(f"오류 발생: {e}")
                break

        # 영상 표시
        cv2.imshow('Received Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    client_socket.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    server_ip = '192.168.0.3'  # Raspberry Pi의 IP 주소 입력
    receive_video(server_ip)
