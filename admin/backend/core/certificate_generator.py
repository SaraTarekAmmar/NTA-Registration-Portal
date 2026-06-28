import os
from typing import Optional

import fitz  # pymupdf
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "uploads")
CERTIFICATES_DIR = os.path.join(UPLOADS_DIR, "certificates")

STAGE_NAMES_AR = {
    1: "مرحلة الفرز",
    2: "مرحلة التحقق الأمني",
    3: "مرحلة التقييم النفسي",
    4: "مرحلة الاختبارات",
    5: "مرحلة المقابلة الأولى",
    6: "مرحلة المقابلة الثانية",
    7: "مرحلة القبول النهائي",
}

STAGE_COLORS = {
    1: (100, 116, 139),  # slate
    2: (234, 88, 12),  # orange
    3: (147, 51, 234),  # purple
    4: (37, 99, 235),  # blue
    5: (5, 150, 105),  # emerald
    6: (21, 128, 61),  # green
    7: (220, 38, 38),  # red
}


def _ensure_cert_dir():
    os.makedirs(CERTIFICATES_DIR, exist_ok=True)


def _insert_text_centered(page, y, text, fontname="helv", fontsize=12, color=(0, 0, 0)):
    """Insert text centered horizontally on the page using TextWriter."""
    rect = page.rect
    tw = fitz.TextWriter(rect)
    font = fitz.Font(fontname)
    tw.append(fitz.Point(0, 0), text, font=font, fontsize=fontsize)
    text_width = tw.text_rect.width
    x = (rect.width - text_width) / 2
    tw.append(fitz.Point(x, y), text, font=font, fontsize=fontsize)
    tw.write_text(page, color=color)


def generate_stage_certificate(
    trainee_name: str,
    stage_id: int,
    national_id: str = "",
    review_date: Optional[str] = None,
):
    """
    Generate a PDF certificate for a completed stage.
    Returns the file path on success, None on failure.
    """
    try:
        _ensure_cert_dir()

        stage_name = STAGE_NAMES_AR.get(stage_id, f"المرحلة {stage_id}")
        r, g, b = STAGE_COLORS.get(stage_id, (100, 116, 139))
        today = review_date or datetime.now().strftime("%Y/%m/%d")
        cert_id = (
            f"NTA-S{stage_id}-{national_id[-6:]}"
            if national_id
            else f"NTA-S{stage_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        doc = fitz.open()
        page = doc.new_page(width=595, height=842)  # A4
        w, h = page.rect.width, page.rect.height

        # Background
        page.draw_rect(fitz.Rect(0, 0, w, h), color=None, fill=(248, 250, 252))

        # Top colored banner
        page.draw_rect(fitz.Rect(0, 0, w, 160), color=None, fill=(r, g, b))

        # Decorative line under banner
        page.draw_rect(
            fitz.Rect(0, 160, w, 164), color=None, fill=(r // 2, g // 2, b // 2)
        )

        # Title text
        _insert_text_centered(
            page, 60, "الأكاديمية الوطنية للتدريب", fontsize=26, color=(1, 1, 1)
        )
        _insert_text_centered(
            page, 95, "National Training Academy", fontsize=14, color=(1, 1, 1)
        )
        _insert_text_centered(
            page, 130, "شهادة إتمام مرحلة", fontsize=18, color=(1, 1, 1)
        )

        # Certificate ID
        _insert_text_centered(
            page, 190, f"رقم الشهادة: {cert_id}", fontsize=10, color=(0.4, 0.4, 0.4)
        )

        # Decorative separator
        page.draw_rect(
            fitz.Rect(w / 2 - 80, 210, w / 2 + 80, 212), color=None, fill=(r, g, b)
        )

        # Body text
        _insert_text_centered(
            page,
            260,
            "تشهد الأكاديمية الوطنية للتدريب بأن",
            fontsize=14,
            color=(0.2, 0.2, 0.2),
        )

        # Trainee name (large)
        _insert_text_centered(
            page, 310, trainee_name, fontsize=22, color=(r / 255, g / 255, b / 255)
        )

        # Underline for name
        name_width = len(trainee_name) * 10
        page.draw_rect(
            fitz.Rect(w / 2 - name_width / 2, 315, w / 2 + name_width / 2, 316),
            color=None,
            fill=(r, g, b),
        )

        # Stage completion text
        _insert_text_centered(
            page,
            360,
            f"لقد أتممت بنجاح {stage_name}",
            fontsize=16,
            color=(0.2, 0.2, 0.2),
        )

        # Date
        _insert_text_centered(
            page, 410, f"تاريخ الإتمام: {today}", fontsize=12, color=(0.4, 0.4, 0.4)
        )

        # Bottom decorative box
        page.draw_rect(
            fitz.Rect(w / 2 - 150, 460, w / 2 + 150, 520),
            color=(r, g, b),
            fill=None,
            width=1.5,
        )
        _insert_text_centered(
            page, 485, f"المرحلة {stage_id} من 7", fontsize=12, color=(0.3, 0.3, 0.3)
        )
        _insert_text_centered(
            page, 505, stage_name, fontsize=14, color=(r / 255, g / 255, b / 255)
        )

        # Footer
        page.draw_rect(fitz.Rect(0, h - 60, w, h), color=None, fill=(30, 41, 59))
        _insert_text_centered(
            page,
            h - 30,
            "جميع الحقوق محفوظة 2026 الأكاديمية الوطنية للتدريب",
            fontsize=9,
            color=(0.6, 0.6, 0.6),
        )

        # Save
        filename = f"cert_s{stage_id}_{national_id[-6:] if national_id else datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        filepath = os.path.join(CERTIFICATES_DIR, filename)
        doc.save(filepath)
        doc.close()

        logger.info(f"Certificate generated: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Failed to generate certificate for stage {stage_id}: {e}")
        return None
