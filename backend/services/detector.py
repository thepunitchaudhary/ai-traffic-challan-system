import cv2
import os

# Path to project root (three levels up: services -> backend -> project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "haarcascade_russian_plate_number.xml")
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = os.path.join(BACKEND_DIR, "uploads")
PLATES_DIR = os.path.join(UPLOADS_DIR, "plates")


def detect_plate(image_path: str) -> str | None:
    """Detect plate from image, save cropped plate, return plate image path."""
    os.makedirs(PLATES_DIR, exist_ok=True)

    img = cv2.imread(image_path)
    if img is None:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    plate_cascade = cv2.CascadeClassifier(MODEL_PATH)
    plates = plate_cascade.detectMultiScale(gray, 1.1, 4)

    for (x, y, w, h) in plates:
        plate_img = img[y:y + h, x:x + w]
        plate_path = os.path.join(PLATES_DIR, "plate.jpg")
        cv2.imwrite(plate_path, plate_img)
        return plate_path

    return None
