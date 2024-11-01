import cv2
import socket
import struct
import pickle
import time
import threading

def start_video_streaming(conn):
    cap = cv2.VideoCapture(0)  # 카메라 장치 열기

    while True:
        try:
            ret, frame = cap.read()
            #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            #frame = cv2.resize(frame, dsize=(160, 160))
            if not ret:
                break
            
            # 이미지 직렬화
            data = pickle.dumps(frame)
            # 데이터 전송
            conn.sendall(struct.pack("L", len(data)) + data)
        
        except (BrokenPipeError, ConnectionResetError) as e:
            print(f"클라이언트와의 연결이 끊어졌습니다: {e}")
            break
        except Exception as e:
            print(f"비디오 전송 중 오류 발생: {e}")
            break

    cap.release()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 5000))  # 포트 5000에서 수신
    server_socket.listen(1)
    print("클라이언트 연결 대기 중...")
    while True:
        try:
            while True:
                conn, addr = server_socket.accept()
                print(f"클라이언트 {addr} 연결됨.")

                # 비디오 스트리밍 쓰레드 시작
                video_thread = threading.Thread(target=start_video_streaming, args=(conn,))
                video_thread.start()

        except Exception as e:
            print(f"서버 오류 발생: {e}")
            conn, addr = server_socket.accept()
            print(f"클라이언트 {addr} 연결됨.")

if __name__ == "__main__":
    start_server()

