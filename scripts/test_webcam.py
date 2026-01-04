import cv2

cap = cv2.VideoCapture(0)

ret, frame = cap.read()
print("Webcam opened:", ret)

if ret:
    cv2.imshow("Test Webcam", frame)
    cv2.waitKey(2000)  # hiện 2 giây

cap.release()
cv2.destroyAllWindows()
