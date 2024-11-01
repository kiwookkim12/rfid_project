import cv2
import socket
import struct
import pickle
import threading
import time
from nav2_simple_commander.robot_navigator import BasicNavigator
import rclpy
from geometry_msgs.msg import PoseStamped

# ROS 2 초기화
rclpy.init()
nav = BasicNavigator()

goal_pose = PoseStamped()

def transform(value, old_min, old_max, new_min, new_max):
    new_value = ((value - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min
    return new_value

    

def handle_coordinates(conn):
    old_min_x = 0
    old_max_x = 1000
    old_min_y = 0
    old_max_y = 600
    new_min_x = -0.22
    new_max_x = 1.25
    new_min_y = -1.23
    new_max_y = 1.16
    global goal_pose  # 전역 변수로 goal_pose 사용
    while True:
        try:
            coord_data = conn.recv(4096)  # 좌표 데이터 수신
            if coord_data:
                coordinates = pickle.loads(coord_data)
                print(f"받은 좌표: {coordinates}")

                # 받은 좌표를 goal_pose에 저장

                goal_pose.header.frame_id = 'map'
                goal_pose.header.stamp = nav.get_clock().now().to_msg()
                goal_pose.pose.position.x = 3.0
                goal_pose.pose.position.x = float(transform(coordinates[0],old_min_x,old_max_x,new_min_x,new_max_x))
                goal_pose.pose.position.y = float(transform(coordinates[1],old_min_y,old_max_y,new_min_y,new_max_y))
                goal_pose.pose.orientation.x = 0.0
                goal_pose.pose.orientation.y = 0.0
                goal_pose.pose.orientation.z = 0.0
                goal_pose.pose.orientation.w = 1.0

                # 목표 위치로 이동
                nav.goToPose(goal_pose)

        except Exception as e:
            print(f"좌표 수신 중 오류 발생: {e}")

def start_video_streaming(conn):
    cap = cv2.VideoCapture(0)  # 카메라 장치 열기
    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                print("카메라에서 프레임을 읽을 수 없습니다.")
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
    #nav.waitUntilNav2Active()

    while True:
        try:
            conn, addr = server_socket.accept()
            print(f"클라이언트 {addr} 연결됨.")

            # 좌표 수신을 위한 쓰레드 시작
            coord_thread = threading.Thread(target=handle_coordinates, args=(conn,))
            coord_thread.start()

            # 비디오 스트리밍 쓰레드 시작
            video_thread = threading.Thread(target=start_video_streaming, args=(conn,))
            video_thread.start()

        except Exception as e:
            print(f"서버 오류 발생: {e}")

if __name__ == "__main__":
    start_server()
