"""OCR image interaction."""

from agentic_navigator.entities.perception.VisualDescription import VisualDescription
from agentic_navigator.interactions.perception.ImageAnalysis import load_image_from_base64


class OCRImage:
    @staticmethod
    def execute(image_base64: str) -> VisualDescription:
        desc = VisualDescription()
        image = load_image_from_base64(image_base64)
        if image is None:
            return desc

        try:
            import pytesseract

            ocr_payload = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            for index, text in enumerate(ocr_payload.get("text", [])):
                cleaned = (text or "").strip()
                if not cleaned:
                    continue

                confidence_raw = ocr_payload.get("conf", [0])[index]
                try:
                    confidence = max(0.0, min(1.0, float(confidence_raw) / 100.0))
                except (TypeError, ValueError):
                    confidence = 0.0

                desc.ocr_text.append(
                    {
                        "text": cleaned,
                        "confidence": round(confidence, 3),
                        "left": ocr_payload.get("left", [0])[index],
                        "top": ocr_payload.get("top", [0])[index],
                        "width": ocr_payload.get("width", [0])[index],
                        "height": ocr_payload.get("height", [0])[index],
                    }
                )

            desc.raw_florence_output = {
                "analysis": "pytesseract-ocr",
                "text_count": len(desc.ocr_text),
            }
        except Exception as exc:
            desc.raw_florence_output = {
                "analysis": "ocr-unavailable",
                "reason": str(exc),
            }
        return desc
