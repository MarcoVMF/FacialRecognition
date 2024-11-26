import cv2
import face_recognition
import pickle
import os
import numpy as np

folderPath = 'Images'
modePathList = os.listdir(folderPath)
imgList = []
studentsId = []

# Load images and student IDs
for path in modePathList:
    imgList.append(cv2.imread(os.path.join(folderPath, path)))
    studentsId.append(os.path.splitext(path)[0])

def findingEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        faceLocations = face_recognition.face_locations(img)
        faceEncodings = face_recognition.face_encodings(img, faceLocations)
        if len(faceEncodings) > 0:
            # Choose the first encoding if there are multiple faces
            encodeList.append(faceEncodings[0])
        else:
            encodeList.append(None)  # handle error if no faces found
    return encodeList

def normalize_encoding(encoding):
    return encoding / np.linalg.norm(encoding)

# Encode images and normalize
encodeListKnowns = findingEncodings(imgList)
encodeListKnowns = [normalize_encoding(encoding) for encoding in encodeListKnowns if encoding is not None]

# Pair encodings with student IDs
encodeListKnownWithIds = [encodeListKnowns, studentsId]


# Save encodings to a file
file = open("EncodeFile.p", "wb")
pickle.dump(encodeListKnownWithIds, file)
file.close()
