import os
import re
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, field_validator

from services.detector import detect_plate
from services.ocr import read_plate
from services.database import get_vehicle_owner, get_fine, get_violations, mark_paid
from services.notification import send_message
from utils.logger import log_challan, get_challan_history

logger = logging.getLogger("challan")
router = APIRouter()

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


class DetectRequest(BaseModel):
    filename: str

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v):
        if not v or not v.strip():
            raise ValueError("Filename cannot be empty")
        return v.strip()


class ChallanRequest(BaseModel):
    plate_number: str
    violation: str

    @field_validator("plate_number")
    @classmethod
    def validate_plate(cls, v):
        if not v or not v.strip():
            raise ValueError("Plate number cannot be empty")
        cleaned = re.sub(r"[^A-Z0-9]", "", v.upper().strip())
        if len(cleaned) < 4:
            raise ValueError("Invalid plate number format")
        return cleaned

    @field_validator("violation")
    @classmethod
    def validate_violation(cls, v):
        if not v or not v.strip():
            raise ValueError("Violation type cannot be empty")
        return v.strip().lower()


class MessageRequest(BaseModel):
    mobile: str
    plate_number: str
    violation: str
    fine: int

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v):
        digits = re.sub(r"\D", "", v)
        if len(digits) < 10:
            raise ValueError("Invalid mobile number")
        return digits[-10:]


class MarkPaidRequest(BaseModel):
    plate: str


@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    logger.info(f"Upload request: {file.filename} ({file.content_type})")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type '.{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    try:
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOADS_DIR, filename)

        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        with open(filepath, "wb") as f:
            f.write(content)

        logger.info(f"Saved: {filename} ({len(content)} bytes)")
        return {"filename": filename, "image_url": f"/uploads/{filename}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded image")


@router.post("/detect-plate")
def detect_plate_api(data: DetectRequest):
    logger.info(f"Detect request: {data.filename}")
    filepath = os.path.join(UPLOADS_DIR, data.filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image not found. Please upload again.")

    try:
        plate_path = detect_plate(filepath)
        if plate_path is None:
            raise HTTPException(status_code=400, detail="No license plate detected in image. Try a clearer photo.")

        plate_number = read_plate(plate_path)
        if plate_number is None:
            raise HTTPException(status_code=400, detail="Could not read plate text. Try a higher resolution image.")

        logger.info(f"Detected plate: {plate_number}")
        return {"plate_number": plate_number, "plate_image_url": "/uploads/plates/plate.jpg"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detection error: {e}")
        raise HTTPException(status_code=500, detail="Plate detection failed due to internal error")


@router.post("/detect-violation")
async def detect_violation_api():
    return {"violation": "overspeed"}


@router.post("/generate-challan")
def generate_challan(data: ChallanRequest):
    logger.info(f"Challan request: plate={data.plate_number}, violation={data.violation}")

    try:
        fine = get_fine(data.violation)
        if fine is None:
            raise HTTPException(status_code=404, detail=f"Violation type '{data.violation}' not found in database")

        owner = get_vehicle_owner(data.plate_number)
        if owner is None:
            raise HTTPException(status_code=404, detail=f"Vehicle '{data.plate_number}' not registered in database")

        log_challan(data.plate_number, data.violation, fine, owner["mobile"])
        logger.info(f"Challan generated for {data.plate_number}: ₹{fine}")

        return {
            "plate_number": data.plate_number,
            "violation": data.violation,
            "fine": fine,
            "owner_name": owner["name"],
            "mobile": owner["mobile"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Challan generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate challan")


@router.post("/send-message")
def send_message_api(data: MessageRequest):
    logger.info(f"Send message: {data.plate_number} → +91{data.mobile}")

    try:
        result = send_message(data.mobile, data.plate_number, data.violation, data.fine)
        return {
            "status": "success",
            "message_text": result["message_text"],
            "payment_link": result["payment_link"],
            "recipient": result["recipient"],
        }
    except Exception as e:
        logger.error(f"Send message error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")


@router.get("/violations")
def list_violations():
    try:
        return {"violations": get_violations()}
    except Exception as e:
        logger.error(f"Violations fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load violation types")


@router.post("/mark-paid")
def mark_paid_api(data: MarkPaidRequest):
    logger.info(f"Mark paid: {data.plate}")
    updated = mark_paid(data.plate)
    if not updated:
        raise HTTPException(status_code=404, detail=f"No unpaid challan found for '{data.plate}'")
    return {"status": "success", "plate": data.plate, "message": "Challan marked as PAID"}


@router.get("/history")
def get_history():
    logger.info("History request")
    try:
        records = get_challan_history()
        return {"history": records}
    except Exception as e:
        logger.error(f"History fetch error: {e}")
        return {"history": []}
