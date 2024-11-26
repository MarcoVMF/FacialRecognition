import os
import bd
import cv2
import time
import pickle
import cvzone
import threading
import numpy as np
import face_recognition
from datetime import datetime
from bd import register_attendance


cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

img_background = cv2.imread('Resources/modes/1.png')

# Setting up the day and discipline

day_translation = {
    "monday": "segunda",
    "tuesday": "terça",
    "wednesday": "quarta",
    "thursday": "quinta",
    "friday": "sexta",
    "saturday": "sábado",
    "sunday": "domingo"
}

now = datetime.now()
day_of_week = now.strftime('%A').lower()
current_hour = now.strftime('%H:%M')

day_of_week = day_translation.get(day_of_week, day_of_week)

# Getting the folders
folderModePath = 'Resources/modes'
modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

# Importing the encoding file
file = open("EncodeFile.p", "rb")
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, studentsId = encodeListKnownWithIds


# Change the background
def change_background(img_background, id, img):
    img_background[0:720, 0:1280] = imgModeList[id]
    img_background[145:145 + 480, 150:150 + 640] = img
    return img_background


# Display the student information
def display_student_info(student_id, img_background):

    student = bd.fetch_student(student_id)
    if not student:
        print(f"Estudante com ID {student_id} não encontrado.")
        cv2.putText(img_background, "Estudante não encontrado", (50, 600),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        return img_background


    student_id, name, degree, image_blob = student


    cv2.putText(img_background, f"{name}", (950, 467),
                cv2.QT_FONT_NORMAL, 0.5, (255, 255, 255), 2)
    cv2.putText(img_background, f"{degree}", (910, 540),
                cv2.QT_FONT_NORMAL, 0.47, (255, 255, 255), 2)


    if image_blob:

        image_np = np.frombuffer(image_blob, dtype=np.uint8)
        student_image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        if student_image is not None:
            student_image = cv2.resize(student_image, (150, 150))  # Adjust size


            x_start, y_start = 935, 190
            x_end, y_end = x_start + 150, y_start + 150


            img_background[y_start:y_end, x_start:x_end] = student_image
        else:
            print("Erro ao carregar a imagem do estudante.")

    return img_background

# Display the modal
def display_modal(img_background, modal_id, student_id, duration=1):
    start_time = cv2.getTickCount()
    while True:
        elapsed_time = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
        if elapsed_time > duration:
            break

        if modal_id == 2:
            img_background[0:720, 0:1280] = imgModeList[modal_id]
            img_background[145:145 + 480, 150:150 + 640] = img

            cv2.imshow("Face Attendance", img_background)
            cv2.waitKey(1)

        elif modal_id == 1:
            img_background[0:720, 0:1280] = imgModeList[modal_id]
            img_background[145:145 + 480, 150:150 + 640] = img

            cv2.imshow("Face Attendance", img_background)
            cv2.waitKey(1)

        else:
            img_background[0:720, 0:1280] = imgModeList[modal_id]
            img_background[145:145 + 480, 150:150 + 640] = img

            cv2.imshow("Face Attendance", img_background)
            cv2.waitKey(1)

    if modal_id == 2:
        return display_modal(img_background, 1, student_id)
    elif modal_id == 1:
        return display_student_info(student_id, img_background)
    else:
        return img_background


# Recognize the faces with threading
lock = threading.Lock()
recognized_faces = []


def recognize_faces():
    global recognized_faces
    while True:
        with lock:
            success, img = cap.read()
            if not success:
                continue
            imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
            imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

            faceCurFrame = face_recognition.face_locations(imgS)
            encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)


        new_recognized_faces = []
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDistance = face_recognition.face_distance(encodeListKnown, encodeFace)

            matchIndex = np.argmin(faceDistance)
            if matches[matchIndex]:
                student_id = int(studentsId[matchIndex])
                new_recognized_faces.append((student_id, faceLoc))


        with lock:
            recognized_faces = new_recognized_faces
        time.sleep(0.05)


recognition_thread = threading.Thread(target=recognize_faces, daemon=True)
recognition_thread.start()


# Main loop
while True:
    with lock:
        success, img = cap.read()
        if not success:
            break

        img_background[145:145 + 480, 150:150 + 640] = img


        for student_id, faceLoc in recognized_faces:
            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            bbox = 145 + x1, 150 + y1, x2 - x1, y2 - y1
            img_background = cvzone.cornerRect(img_background, bbox, rt=0)


            try:
                discipline_id = bd.fetchDisciplineByHourAndDay(student_id, day_of_week, current_hour)
                id = register_attendance(student_id, discipline_id)
                img_background = display_modal(img_background, id, student_id)
            except Exception as e:
                print(f"Erro ao registrar frequência: {e}")

    cv2.imshow("Face Attendance", img_background)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()