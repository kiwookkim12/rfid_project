import mysql.connector
import serial
import time
from datetime import datetime, timedelta
import re

class DogHotelSystem:
    def __init__(self):
        """시스템 초기화 및 시리얼 포트 설정"""
        self.db = None
        self.cursor = None
        try:
            self.serial_port = serial.Serial(
                port='/dev/ttyUSB0',  # 시스템에 맞게 포트 수정 필요
                baudrate=9600,
                timeout=1
            )
        except serial.SerialException as e:
            print(f"시리얼 포트 연결 실패: {e}")
            self.serial_port = None

    def connect_to_db(self):
        """데이터베이스 연결"""
        try:
            self.db = mysql.connector.connect(
                host="localhost",
                user="kw",
                password="1111",
                database="dogdb",
                autocommit=True
            )
            self.cursor = self.db.cursor(dictionary=True)
            print("데이터베이스 연결 성공")
        except mysql.connector.Error as e:
            print(f"데이터베이스 연결 실패: {e}")
            raise

    def clean_rfid(self, rfid_string):
        """RFID 문자열에서 UID만 추출하고 16진법으로 변환"""
        if not rfid_string:
            return None
            
        # 문자열 타입 확인 및 변환
        if not isinstance(rfid_string, str):
            try:
                rfid_string = str(rfid_string)
            except:
                return None
                
        # 불필요한 텍스트 제거
        remove_texts = [
            "태그의 NUID는 다음과 있습니다:",
            "태그의 NUID는 다음과 함께있습니다:",
            "새로운 태그가 인식되었습니다.",
            "\n",
            "\r"
        ]
        
        for text in remove_texts:
            rfid_string = rfid_string.replace(text, "")
        
        # PICC 타입 정보가 있는 경우 처리
        if "PICC type: " in rfid_string:
            try:
                rfid_string = rfid_string.split("PICC type: ")[-1].strip()
            except:
                return None
        
        # 공백 제거 및 문자열 정리
        rfid_string = rfid_string.strip()
        
        # 16진수 문자열만 추출 (정규식 사용)
        hex_pattern = re.compile(r'[0-9A-Fa-f]+')
        matches = hex_pattern.findall(rfid_string)
        
        if not matches:
            return None
            
        # 가장 긴 16진수 문자열 선택 (일반적으로 UID)
        rfid_string = max(matches, key=len)
        
        try:
            # 문자열 길이가 짝수가 아닌 경우 패딩 추가
            if len(rfid_string) % 2 != 0:
                rfid_string = '0' + rfid_string
                
            # 16진수 변환 검증
            uid_bytes = bytes.fromhex(rfid_string)
            return uid_bytes.hex().upper()
        except ValueError:
            return None

    def read_rfid(self):
        """RFID 카드 읽기"""
        if not self.serial_port:
            print("시리얼 포트가 연결되지 않았습니다.")
            return None

        print("RFID 카드를 스캔해 주세요...")
        max_attempts = 3
        attempt_count = 0
        
        while attempt_count < max_attempts:
            try:
                if not self.serial_port.is_open:
                    self.serial_port.open()
                    
                if self.serial_port.in_waiting:
                    card_uid = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if card_uid:
                        clean_uid = self.clean_rfid(card_uid)
                        if clean_uid:
                            print(f"카드 UID: {clean_uid}")
                            return clean_uid
                        else:
                            print("유효하지 않은 카드 형식입니다. 다시 시도해 주세요.")
                            attempt_count += 1
                time.sleep(0.1)
                
            except serial.SerialException as e:
                print(f"시리얼 포트 오류: {e}")
                return None
            except UnicodeDecodeError:
                print("카드 데이터 읽기 오류. 다시 시도해 주세요.")
                attempt_count += 1
        
        print("최대 시도 횟수를 초과했습니다.")
        return None

    def register_new_dog(self):
        """새로운 강아지 등록"""
        try:
            # 보호자 정보 입력
            print("\n=== 보호자 정보 입력 ===")
            owner_name = input("보호자 이름: ")
            owner_gender = input("보호자 성별: ")
            owner_birth_date = input("보호자 생년월일: ")
            owner_phone = input("연락처: ")
            owner_address = input("주소: ")
            
            # 보호자 정보 저장
            owner_query = """
            INSERT INTO customer_information (name, gender, birth_date, phone_number, address)
            VALUES (%s, %s, %s, %s, %s)
            """
            # Corrected the parameters to match the placeholders
            self.cursor.execute(owner_query, (owner_name, owner_gender, owner_birth_date, owner_phone, owner_address))
            customer_id = self.cursor.lastrowid
            
            # RFID 카드 읽기
            print("\nRFID 카드를 등록하겠습니다.")
            card_uid = self.read_rfid()
            if not card_uid:
                print("카드 등록 실패")
                self.db.rollback()
                return
                
            # 강아지 정보 입력
            print("\n=== 강아지 정보 입력 ===")
            dog_name = input("강아지 이름: ")
            dog_breed = input("품종: ")
            dog_gender = input("성별 (M/F): ").upper()
            birth_date = input("생년월일 (YYYY-MM-DD): ")
            dog_neutered = input("중성화 여부 (Y/N): ").upper() == 'Y'
            dog_health_issue = input("건강 문제 (없으면 엔터): ") or None
            dog_vaccination_status = input("예방접종 현황: ")
            dog_remarks = input("특이사항 (없으면 엔터): ") or None
            
            # 강아지 정보 저장
            dog_query = """
            INSERT INTO dog_information 
            (customer_id, rfid_uid, dog_name, dog_breed, dog_gender, birth_date,
            dog_neutered, dog_health_issue, dog_vaccination_status, dog_remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            self.cursor.execute(dog_query, (
                customer_id, card_uid, dog_name, dog_breed, dog_gender, birth_date,
                dog_neutered, dog_health_issue, dog_vaccination_status, dog_remarks
            ))
            
            self.db.commit()  # Don't forget to commit the changes
            
            print("\n강아지 등록이 완료되었습니다!")
            
        except Exception as e:
            print(f"등록 중 오류가 발생했습니다: {e}")
            self.db.rollback()

    def check_dog_info(self):
        """RFID를 사용하여 강아지 정보 조회"""
        try:
            card_uid = self.read_rfid()
            if card_uid is None:
                print("RFID 카드 인식 실패. 강아지 정보를 조회할 수 없습니다.")
                return
            
            # RFID UID로 강아지 정보를 조회
            query = """
            SELECT 
                c.name AS owner_name,
                c.gender AS owner_gender,
                c.birth_date AS owner_birth_date,
                c.phone_number AS owner_phone,
                d.dog_name, 
                d.dog_breed, 
                d.dog_gender, 
                d.birth_date,
                d.dog_neutered, 
                d.dog_health_issue, 
                d.dog_vaccination_status, 
                d.dog_remarks
            FROM dog_information d
            JOIN customer_information c ON d.customer_id = c.id
            WHERE d.rfid_uid = %s
            """
            
            self.cursor.execute(query, (card_uid,))
            dog_info = self.cursor.fetchone()

            if dog_info:
                print("\n=== 강아지 정보 ===")
                fields = [
                    ('보호자 이름', 'owner_name'),
                    ('보호자 생년월일', lambda x: x['owner_birth_date'].strftime('%Y-%m-%d')),
                    ('보호자 성별', lambda x: '남성' if x['owner_gender'] == 'M' else '여성'),
                    ('보호자 연락처', 'owner_phone'),
                    ('강아지 이름', 'dog_name'),
                    ('품종', 'dog_breed'),
                    ('성별', lambda x: '수컷' if x['dog_gender'] == 'M' else '암컷'),
                    ('생년월일', lambda x: x['birth_date'].strftime('%Y-%m-%d')),
                    ('중성화 여부', lambda x: '예' if x['dog_neutered'] == 1 else '아니오'),
                    ('건강 문제', lambda x: x['dog_health_issue'] if x['dog_health_issue'] else '없음'),
                    ('예방 접종 상태', 'dog_vaccination_status'),
                    ('비고', lambda x: x['dog_remarks'] if x['dog_remarks'] else '없음')
                ]
                
                for label, field in fields:
                    value = field(dog_info) if callable(field) else dog_info[field]
                    print(f"{label}: {value}")
            else:
                print("등록되지 않은 카드입니다. 강아지 정보를 찾을 수 없습니다.")
                
        except Exception as e:
            print(f"오류가 발생했습니다: {e}")
            self.db.rollback()

    def check_in_dog(self):
        """강아지 체크인"""
        try:
            print("\n=== 강아지 체크인 ===")
            card_uid = self.read_rfid()
            if not card_uid:
                return
            
            # Check if the dog is already checked in
            check_query = """
            SELECT d.dog_name 
            FROM check_in_status cs
            JOIN dog_information d ON cs.dog_name = d.dog_name
            WHERE d.rfid_uid = %s AND cs.check_out IS NULL
            """
            self.cursor.execute(check_query, (card_uid,))
            existing_check_in = self.cursor.fetchone()
            
            if existing_check_in:
                print(f"{existing_check_in['dog_name']}은 이미 체크인되어 있습니다.")
                return
                
            # Get dog info
            info_query = """
            SELECT d.dog_name, c.id AS customer_id, c.name AS owner_name 
            FROM dog_information d 
            JOIN customer_information c ON d.customer_id = c.id 
            WHERE d.rfid_uid = %s
            """
            self.cursor.execute(info_query, (card_uid,))
            dog_info = self.cursor.fetchone()
            
            if not dog_info:
                print("등록되지 않은 카드입니다.")
                return
                
            # Check-in information
            expected_check_out = input("예상 체크아웃 날짜와 시간 (YYYY-MM-DD HH:MM): ")
            special_notes = input("특이사항 (없으면 엔터): ") or None
            
            # Insert check-in status
            insert_query = """
            INSERT INTO check_in_status (customer_id, name, dog_name, check_in, check_out, remarks)
            VALUES (%s, %s, %s, NOW(), NULL, %s)
            """
            self.cursor.execute(insert_query, (dog_info['customer_id'], dog_info['owner_name'], dog_info['dog_name'], special_notes))
            self.db.commit()

            print(f"\n{dog_info['dog_name']}의 체크인이 완료되었습니다!")
            
        except Exception as e:
            print(f"체크인 중 오류가 발생했습니다: {e}")
            self.db.rollback()

    def check_out_dog(self):
        """강아지 체크아웃"""
        try:
            print("\n=== 강아지 체크아웃 ===")
            card_uid = self.read_rfid()
            if not card_uid:
                return
                
            # Check-out processing with JOIN to access rfid_uid in dog_information
            check_query = """
            SELECT cs.id, d.dog_name, cs.check_in AS check_in_time 
            FROM check_in_status cs
            JOIN dog_information d ON cs.dog_name = d.dog_name
            WHERE d.rfid_uid = %s AND cs.check_out IS NULL
            """
            self.cursor.execute(check_query, (card_uid,))
            check_in_info = self.cursor.fetchone()
            
            if not check_in_info:
                print("체크인 기록이 없는 카드입니다.")
                return
                
            # Calculate the stay duration
            stay_duration = datetime.now() - check_in_info['check_in_time']
            print(f"체류 시간: {stay_duration}")
            
        
            # Update check-out information in the database
            checkout_query = """
            UPDATE check_in_status
            SET check_out = %s
            WHERE id = %s
            """
            self.cursor.execute(checkout_query, (datetime.now(), check_in_info['id']))
            self.db.commit()

            print(f"{check_in_info['dog_name']}의 체크아웃이 완료되었습니다!")
            
        except Exception as e:
            print(f"체크아웃 중 오류가 발생했습니다: {e}")
            self.db.rollback()

    def check_in_logs(self):
        """최근 체크인 기록 조회"""
        try:
            print("\n=== 최근 체크인 기록 ===")
            query = """
            SELECT 
                d.dog_name,
                c.name AS owner_name,
                cs.check_in AS check_in_time,
                cs.check_out AS check_out_time,
                cs.remarks AS special_notes
            FROM check_in_status cs
            JOIN dog_information d ON cs.dog_name = d.dog_name
            JOIN customer_information c ON cs.customer_id = c.id
            ORDER BY cs.check_in DESC
            LIMIT 10
            """
            self.cursor.execute(query)
            logs = self.cursor.fetchall()
            
            if not logs:
                print("체크인 기록이 없습니다.")
                return
                
            for log in logs:
                print("\n---")
                print(f"강아지 이름: {log['dog_name']}")
                print(f"보호자 이름: {log['owner_name']}")
                print(f"체크인 시간: {log['check_in_time'].strftime('%Y-%m-%d %H:%M')}")
                if log['check_out_time']:
                    print(f"체크아웃 시간: {log['check_out_time'].strftime('%Y-%m-%d %H:%M')}")
                else:
                    print("체크아웃 상태: 체류중")
                if log['special_notes']:
                    print(f"특이사항: {log['special_notes']}")
                    
        except Exception as e:
            print(f"기록 조회 중 오류가 발생했습니다: {e}")

    def delete_card(self, card_uid):
        """카드 정보 삭제"""
        try:
            # 카드 정보 확인
            check_query = """
            SELECT d.dog_name, c.name AS owner_name
            FROM dog_information d
            JOIN customer_information c ON d.customer_id = c.id
            WHERE d.rfid_uid = %s
            """
            self.cursor.execute(check_query, (card_uid,))
            card_info = self.cursor.fetchone()
            
            if not card_info:
                print("등록되지 않은 카드입니다.")
                return
                
            # 삭제 확인
            print(f"\n카드 정보:")
            print(f"강아지 이름: {card_info['dog_name']}")
            print(f"보호자 이름: {card_info['owner_name']}")
            
            confirm = input("\n이 카드를 정말 삭제하시겠습니까? (Y/N): ").upper()
            if confirm != 'Y':
                print("삭제가 취소되었습니다.")
                return
                
            # 관련 체크인 로그 삭제
            log_delete_query = "DELETE FROM check_in_logs WHERE rfid_uid = %s"
            self.cursor.execute(log_delete_query, (card_uid,))
            
            # 강아지 정보 삭제
            dog_delete_query = "DELETE FROM dog_information WHERE rfid_uid = %s"
            self.cursor.execute(dog_delete_query, (card_uid,))
            
            print("카드가 성공적으로 삭제되었습니다.")
            
        except Exception as e:
            print(f"카드 삭제 중 오류가 발생했습니다: {e}")
            self.db.rollback()

    def close_connection(self):
        """데이터베이스 연결 종료"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.db:
                self.db.close()
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            print("모든 연결이 안전하게 종료되었습니다.")
        except Exception as e:
            print(f"연결 종료 중 오류가 발생했습니다: {e}")

    def shutdown(self):
        # Clean-up and shutdown logic (e.g., close DB connections)
        print("모든 연결이 안전하게 종료되었습니다.")
        if self.db:
            self.db.close()        

if __name__ == '__main__':
    dog_hotel_system = None
    try:
        dog_hotel_system = DogHotelSystem()
        dog_hotel_system.connect_to_db()
        
        while True:
            print("\n=== 강아지 호텔 시스템 ===")
            print("1. 고객정보 및 새 강아지 등록")
            print("2. 강아지 정보 확인")
            print("3. 강아지 체크인")
            print("4. 강아지 체크아웃")
            print("5. 최근 체크인 기록 조회")
            print("6. 카드 삭제")
            print("7. 종료")
            
            try:
                choice = input("\n원하는 작업을 선택해 주세요: ").strip()
                
                if choice == '1':
                    dog_hotel_system.register_new_dog()
                elif choice == '2':
                    dog_hotel_system.check_dog_info()
                elif choice == '3':
                    dog_hotel_system.check_in_dog()
                elif choice == '4':
                    dog_hotel_system.check_out_dog()
                elif choice == '5':
                    dog_hotel_system.check_in_logs()
                elif choice == '6':
                    card_uid = input("삭제할 카드의 UID를 입력해 주세요: ")
                    dog_hotel_system.delete_card(card_uid)
                elif choice == '7':
                    print("\n시스템을 종료합니다. 감사합니다!")
                    break
                else:
                    print("\n잘못된 선택입니다. 다시 시도해 주세요.")
                    
            except ValueError as e:
                print(f"\n입력 오류: {e}")
                continue
                
    except Exception as e:
        print(f"시스템 실행 중 오류가 발생했습니다: {e}")
        
    finally:
        if dog_hotel_system:
            dog_hotel_system.close_connection()


