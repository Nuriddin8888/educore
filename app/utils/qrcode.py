import qrcode
import base64
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib import colors
from reportlab.lib.units import mm


# ── Colours ──────────────────────────────────────────────────
DARK   = (15/255, 15/255, 18/255)       # header bg
ACCENT = (99/255, 102/255, 241/255)     # indigo
LIGHT  = (249/255, 250/255, 251/255)    # footer bg
BORDER = (229/255, 231/255, 235/255)
MUTED  = (156/255, 163/255, 175/255)
BLACK  = (17/255, 24/255, 39/255)
WHITE  = (1, 1, 1)


def _set_fill(c, rgb):
    c.setFillColorRGB(*rgb)

def _set_stroke(c, rgb):
    c.setStrokeColorRGB(*rgb)

def _rounded_rect(c, x, y, w, h, r, fill=None, stroke=None, line_width=1):
    """Draw a rounded rectangle (fill and/or stroke)."""
    if fill:
        _set_fill(c, fill)
    if stroke:
        _set_stroke(c, stroke)
        c.setLineWidth(line_width)

    p = c.beginPath()
    p.moveTo(x + r, y)
    p.lineTo(x + w - r, y)
    p.arcTo(x + w - 2*r, y, x + w, y + 2*r, startAng=-90, extent=90)
    p.lineTo(x + w, y + h - r)
    p.arcTo(x + w - 2*r, y + h - 2*r, x + w, y + h, startAng=0, extent=90)
    p.lineTo(x + r, y + h)
    p.arcTo(x, y + h - 2*r, x + 2*r, y + h, startAng=90, extent=90)
    p.lineTo(x, y + r)
    p.arcTo(x, y, x + 2*r, y + 2*r, startAng=180, extent=90)
    p.close()

    mode = 0
    if fill and stroke:
        mode = 3        # fill + stroke
    elif fill:
        mode = 1        # fill only
    elif stroke:
        mode = 2        # stroke only
    c.drawPath(p, fill=(1 if fill else 0), stroke=(1 if stroke else 0))


def _qr_image_reader(code: str, size_px: int = 300) -> ImageReader:
    qr = qrcode.QRCode(border=1)
    qr.add_data(code)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img = img.resize((size_px, size_px))
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def generate_card_pdf(
    full_name: str,
    student_id: str,
    password: str,
    code: str,
) -> bytes:
    """
    Returns the PDF as raw bytes.
    Card is rendered directly with ReportLab — no PIL rasterisation,
    so text is crisp at any zoom level.
    """
    # ── Card dimensions (A6-ish, portrait) ──────────────────
    CW, CH = 85*mm, 120*mm          # card width / height
    CORNER = 6                       # rounded corner radius (pt)

    # ── A4 page, card centred ────────────────────────────────
    PW, PH = A4
    ox = (PW - CW) / 2              # card origin X
    oy = (PH - CH) / 2              # card origin Y

    buf = BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"Student Card – {full_name}")

    # ── Card background ──────────────────────────────────────
    _rounded_rect(c, ox, oy, CW, CH, CORNER, fill=WHITE, stroke=BORDER, line_width=0.5)

    # ── Header block ────────────────────────────────────────
    HEADER_H = 32*mm
    c.saveState()
    # clip to card so header rounded corners are hidden under the card bg
    p = c.beginPath()
    p.rect(ox, oy + CH - HEADER_H, CW, HEADER_H)
    c.clipPath(p, stroke=0)
    _rounded_rect(c, ox, oy + CH - HEADER_H, CW, HEADER_H, CORNER, fill=DARK)
    c.restoreState()

    # "IT SCHOOL" badge
    BADGE_X = ox + 6*mm
    BADGE_Y = oy + CH - 10*mm
    badge_text = "IT SCHOOL"
    c.setFont("Helvetica-Bold", 7)
    tw = c.stringWidth(badge_text, "Helvetica-Bold", 7)
    _rounded_rect(c, BADGE_X - 2, BADGE_Y - 2, tw + 16, 10, 3, fill=ACCENT)
    _set_fill(c, WHITE)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(BADGE_X + 6, BADGE_Y + 1, badge_text)

    # Full name
    parts = full_name.strip().split(" ", 1)
    _set_fill(c, WHITE)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(ox + 6*mm, oy + CH - 20*mm, parts[0])
    if len(parts) == 2:
        c.setFont("Helvetica", 12)
        c.drawString(ox + 6*mm, oy + CH - 26*mm, parts[1])

    # ── QR code ─────────────────────────────────────────────
    QR_SIZE = 38*mm
    QR_X = ox + (CW - QR_SIZE) / 2
    QR_Y = oy + CH - HEADER_H - QR_SIZE - 8*mm

    # thin border around QR
    _rounded_rect(c, QR_X - 2, QR_Y - 2, QR_SIZE + 4, QR_SIZE + 4, 4,
                  fill=WHITE, stroke=BORDER, line_width=0.5)
    qr_reader = _qr_image_reader(code, size_px=400)
    c.drawImage(qr_reader, QR_X, QR_Y, width=QR_SIZE, height=QR_SIZE,
                preserveAspectRatio=True, mask="auto")

    # ── Divider ──────────────────────────────────────────────
    DIV_Y = QR_Y - 6*mm
    _set_stroke(c, BORDER)
    c.setLineWidth(0.5)
    c.line(ox + 6*mm, DIV_Y, ox + CW - 6*mm, DIV_Y)

    # ── Info cells (ID + Password) ────────────────────────────
    CELL_Y  = DIV_Y - 18*mm
    CELL_H  = 14*mm
    PAD     = 6*mm
    GAP     = 3*mm
    CELL_W  = (CW - PAD*2 - GAP) / 2

    for i, (label, value) in enumerate([("ID", str(student_id)), ("PASSWORD", password)]):
        cx = ox + PAD + i * (CELL_W + GAP)
        _rounded_rect(c, cx, CELL_Y, CELL_W, CELL_H, 4,
                      fill=LIGHT, stroke=BORDER, line_width=0.5)
        # label
        _set_fill(c, MUTED)
        c.setFont("Helvetica", 6)
        c.drawString(cx + 3*mm, CELL_Y + CELL_H - 4.5*mm, label)
        # value
        _set_fill(c, BLACK)
        c.setFont("Courier-Bold", 9)
        # shrink font if value is too wide
        font_size = 9
        while c.stringWidth(value, "Courier-Bold", font_size) > CELL_W - 6*mm and font_size > 5:
            font_size -= 0.5
        c.setFont("Courier-Bold", font_size)
        c.drawString(cx + 3*mm, CELL_Y + 3*mm, value)

    # ── Footer ───────────────────────────────────────────────
    FOOT_H = 8*mm
    c.saveState()
    p = c.beginPath()
    p.rect(ox, oy, CW, FOOT_H)
    c.clipPath(p, stroke=0)
    _rounded_rect(c, ox, oy, CW, FOOT_H, CORNER, fill=LIGHT)
    c.restoreState()

    _set_stroke(c, BORDER)
    c.setLineWidth(0.5)
    c.line(ox, oy + FOOT_H, ox + CW, oy + FOOT_H)

    _set_fill(c, MUTED)
    c.setFont("Helvetica", 6)
    c.drawString(ox + 6*mm, oy + 2.5*mm, "STUDENT CARD")

    # three dots (accent decoration)
    for di in range(3):
        dx = ox + CW - 10*mm + di * 3.5*mm
        _set_fill(c, ACCENT if di == 0 else BORDER)
        c.circle(dx, oy + 4*mm, 1.5, fill=1, stroke=0)

    c.save()
    return buf.getvalue()


# ── Convenience helpers ──────────────────────────────────────

def generate_qr_base64(full_name, student_id, password, code) -> str:
    return base64.b64encode(generate_card_pdf(full_name, student_id, password, code)).decode()


def save_card_as_pdf(full_name, student_id, password, code, output_path: str):
    with open(output_path, "wb") as f:
        f.write(generate_card_pdf(full_name, student_id, password, code))
    print(f"PDF saqlandi: {output_path}")
