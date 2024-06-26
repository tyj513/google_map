from flask import Flask, render_template, request
import cv2
import mediapipe as mp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
import speech_recognition as sr
import threading
import time
import sys

app = Flask(__name__)

# Initialize MediaPipe and Selenium components
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils

chrome_driver_path = r"C:\Users\ben20415\Desktop\chromedriver.exe"
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service)

street_view_url = 'https://www.google.com/maps/@22.7368195,121.066442,3a,75y,95.84h,85.02t/data=!3m8!1e1!3m6!1sAF1QipPAgkMGdgnzqW9tcnKNkMAX76Wy16tiTOKpb9d4!2e10!3e11!6shttps:%2F%2Flh5.googleusercontent.com%2Fp%2FAF1QipPAgkMGdgnzqW9tcnKNkMAX76Wy16tiTOKpb9d4%3Dw203-h100-k-no-pi0.04668052-ya80.99285-ro-0.35289368-fo100!7i5760!8i2880?authuser=0&coh=205409&entry=ttu'
driver.get(street_view_url)

def move_forward():
    # Function to move Google Street View forward
    try:
        canvas = driver.find_element(By.CSS_SELECTOR, 'canvas.widget-scene-canvas')
        canvas.click()
        canvas.send_keys(Keys.ARROW_UP)
    except Exception as e:
        print(f"Failed to move forward: {e}")

# Add more control functions (move_backward, control_google_street_view, etc.)
def move_backward():
    try:
        canvas = driver.find_element(By.CSS_SELECTOR, 'canvas.widget-scene-canvas')
        canvas.click()
        canvas.send_keys(Keys.ARROW_DOWN)
    except Exception as e:
        print(f"Failed to move backward: {e}")
def control_google_street_view(command):
    if command == "forward":
        move_forward()
    elif command == "backward":
        move_backward()
    elif command == "left":
        left_button = driver.find_element(By.XPATH, '//button[@aria-label="逆時針旋轉檢視畫面"]')
        left_button.click()
    elif command == "right":
        right_button = driver.find_element(By.XPATH, '//button[@aria-label="順時針旋轉檢視畫面"]')
        right_button.click()
    elif command == "large":
        left_button = driver.find_element(By.XPATH, '//button[@aria-label="放大"]')
        left_button.click()
    elif command == "small":
        right_button = driver.find_element(By.XPATH, '//button[@aria-label="縮小"]')
        right_button.click()
    time.sleep(1)

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == "POST":
        # Run your Python script here or call the necessary functions
        detect_hands()
        recognize_speech()
        return "Script executed successfully"  # Or return some meaningful response

    return render_template('index.html')


def detect_hands():
    cap = cv2.VideoCapture(0)
    
    with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as hands:
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Convert the BGR image to RGB.
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame and detect hands.
            results = hands.process(frame)
            
            # Draw the hand annotations on the frame.
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            




            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # 繪製手部關鍵點
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    # 提取關鍵點
                    for landmark_id, landmark in enumerate(hand_landmarks.landmark):
                        # 將關鍵點坐標轉換為畫面上的像素坐標
                        cx, cy = int(landmark.x * frame.shape[1]), int(landmark.y * frame.shape[0])
                        
                        # 標示關鍵點
                        cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
                        
                        # 在圓圈旁邊標示關鍵點 ID 和坐標
                        cv2.putText(frame, f'{landmark_id} ({cx}, {cy})', (cx - 25, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                    
                    # 設置手掌朝向檢測
                    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    index_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]
                    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]

                    # 計算相對位置
                    thumb_rel_y = thumb_tip.y - wrist.y
                    index_rel_y = index_tip.y - wrist.y
                    index_mcp_rel_y = index_mcp.y - wrist.y

                    thumb_rel_x = thumb_tip.x - wrist.x
                    index_rel_x = index_tip.x - wrist.x

                    # 檢測手掌朝向
                    if index_tip.y < index_mcp.y:  # 手掌向上
                        if thumb_rel_y < index_rel_y:
                            control_google_street_view("forward")
                            cv2.putText(frame, 'Forward', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                        elif thumb_rel_y > index_rel_y:
                            control_google_street_view("backward")
                            cv2.putText(frame, 'Backward', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                    else:  # 手掌向下
                        if thumb_rel_x < wrist.x:
                            control_google_street_view("left")
                            cv2.putText(frame, 'Left', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                        elif thumb_rel_x > wrist.x:
                            control_google_street_view("right")
                            cv2.putText(frame, 'Right', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

                    # 繪製手掌朝向線
                    cv2.line(frame, (int(wrist.x * frame.shape[1]), int(wrist.y * frame.shape[0])), (int(thumb_tip.x * frame.shape[1]), int(thumb_tip.y * frame.shape[0])), (0, 255, 0), 2)
                    cv2.line(frame, (int(wrist.x * frame.shape[1]), int(wrist.y * frame.shape[0])), (int(index_tip.x * frame.shape[1]), int(index_tip.y * frame.shape[0])), (0, 255, 0), 2)
                    cv2.line(frame, (int(wrist.x * frame.shape[1]), int(wrist.y * frame.shape[0])), (int(index_mcp.x * frame.shape[1]), int(index_mcp.y * frame.shape[0])), (0, 255, 0), 2)

                            
                    cv2.imshow('MediaPipe Hands', frame)
                    
                    if cv2.waitKey(10) & 0xFF == ord('q'):
                        break
    
    cap.release()
    cv2.destroyAllWindows()
    sys.exit()

# Function for speech recognition
def recognize_speech():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    while True:
        with mic as source:
            print("Adjusting for ambient noise, please wait...")
            recognizer.adjust_for_ambient_noise(source)
            print("Listening...")

            audio = recognizer.listen(source)
            
            try:
                print("Recognizing speech...")
                text = recognizer.recognize_google(audio, language="zh-TW")
              #  text = recognizer.recognize_google(audio, language="en-US")
                print("You said: " + text)
                if "前進" in text:
                    control_google_street_view("forward")
                elif "後退" in text:
                    control_google_street_view("backward")
                elif "左轉" in text:
                    control_google_street_view("left")
                elif "右轉" in text:
                    control_google_street_view("right")
                elif "放大" in text:
                    control_google_street_view("large")
                elif "縮小" in text:
                    control_google_street_view("small")
                elif "結束" in text:
                    sys.exit()
                elif "前往圖書館" in text:
                    street_view_url = 'https://www.google.com/maps/@22.7356212,121.0672933,3a,79.5y,60.22h,86.35t/data=!3m8!1e1!3m6!1sAF1QipOPmPB89lw2hIGGKTIXzzq9dXk3qNEse8VdiATI!2e10!3e11!6shttps:%2F%2Flh5.googleusercontent.com%2Fp%2FAF1QipOPmPB89lw2hIGGKTIXzzq9dXk3qNEse8VdiATI%3Dw900-h600-k-no-pi3.6529637277848366-ya323.26367792516066-ro0.1947021484375-fo90!7i5760!8i2880?authuser=0&coh=205410&entry=ttu'
                    driver.get(street_view_url)
                elif "前往宿舍" in text:
                    street_view_url = 'https://www.google.com/maps/@22.7370236,121.0651851,3a,75y,24.23h,91.82t/data=!3m8!1e1!3m6!1sAF1QipNog5E2SRIzRD4FvA4ZnqHRxkvUvkkI3UOEaG_z!2e10!3e11!6shttps:%2F%2Flh5.googleusercontent.com%2Fp%2FAF1QipNog5E2SRIzRD4FvA4ZnqHRxkvUvkkI3UOEaG_z%3Dw900-h600-k-no-pi-1.8158282760946634-ya21.39081343560405-ro1.076060652732849-fo90!7i5760!8i2880?authuser=0&coh=205410&entry=ttu'
                    driver.get(street_view_url)

                elif "前往鏡心湖" in text:
                    street_view_url = 'https://www.google.com/maps/@22.734968,121.0669146,3a,75y,90h,79.93t/data=!3m8!1e1!3m6!1sAF1QipMnwpsidZQ4UZVKM0A7NnYydsPYsEuoP3oEAZlN!2e10!3e11!6shttps:%2F%2Flh5.googleusercontent.com%2Fp%2FAF1QipMnwpsidZQ4UZVKM0A7NnYydsPYsEuoP3oEAZlN%3Dw900-h600-k-no-pi10.073601362242272-ya76.42426872253418-ro1.5650634765625-fo90!7i5760!8i2880?authuser=0&coh=205410&entry=ttu'
                    driver.get(street_view_url)

                elif "前往校門口" in text:
                    street_view_url = 'https://www.google.com/maps/@22.7368429,121.0699786,3a,75y,221.23h,86.93t/data=!3m8!1e1!3m6!1sAF1QipO9LmD0MXavgLkjl76RHI7omuOUmQrddq6WZEOR!2e10!3e11!6shttps:%2F%2Flh5.googleusercontent.com%2Fp%2FAF1QipO9LmD0MXavgLkjl76RHI7omuOUmQrddq6WZEOR%3Dw900-h600-k-no-pi3.06541915644452-ya353.73019578771584-ro0.118316650390625-fo90!7i5760!8i2880?authuser=0&coh=205410&entry=ttu'
                    driver.get(street_view_url)

            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print("Error with the recognition service; {0}".format(e))

hand_thread = threading.Thread(target=detect_hands)
speech_thread = threading.Thread(target=recognize_speech)

hand_thread.start()
speech_thread.start()

hand_thread.join()
speech_thread.join()

if __name__ == '__main__':
    app.run(debug=True)
                              