import cv2
import face_recognition
import pickle
import os

folderPath = 'Images'
modePathList = os.listdir(folderPath)
imgList = []
studentsId = []
for path in modePathList:
    imgList.append(cv2.imread(os.path.join(folderPath, path)))
    studentsId.append(os.path.splitext(path)[0])

def findingEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)

    return encodeList


encodeListKnowns = findingEncodings(imgList)
encodeListKnownWithIds = [encodeListKnowns, studentsId]

file = open("EncodeFile.p", "wb")
pickle.dump(encodeListKnownWithIds, file)
file.close()