import cv2

kamera = cv2.VideoCapture(0,cv2.CAP_DSHOW)

if not kamera.isOpened():
    print("Kamera açılamadı.")
    exit()

while True:
    ok,frame = kamera.read()
    if not ok:
        print("Kare okunamadı.")
        break

    cv2.imshow("Kamera", frame)
    if  cv2.waitKey(1) & 0xFF == ord("q"):
        break

kamera.release()
cv2.destroyAllWindows()