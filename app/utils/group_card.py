import qrcode
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm

# ── Colours ──────────────────────────────────────────────────
DARK   = (15/255,  15/255,  18/255)
ACCENT = (99/255, 102/255, 241/255)
LIGHT  = (249/255, 250/255, 251/255)
BORDER = (229/255, 231/255, 235/255)
MUTED  = (156/255, 163/255, 175/255)
BLACK  = (17/255,  24/255,  39/255)
WHITE  = (1, 1, 1)

PW, PH = A4   # 595 x 841 pt


# ── Helpers ───────────────────────────────────────────────────
def sf(c, rgb): c.setFillColorRGB(*rgb)
def ss(c, rgb): c.setStrokeColorRGB(*rgb)

def rrect(c, x, y, w, h, r, fill=None, stroke=None, lw=0.5):
    if fill:   sf(c, fill)
    if stroke: ss(c, stroke); c.setLineWidth(lw)
    p = c.beginPath()
    p.moveTo(x+r, y);          p.lineTo(x+w-r, y)
    p.arcTo(x+w-2*r, y,       x+w, y+2*r,       startAng=-90, extent=90)
    p.lineTo(x+w, y+h-r)
    p.arcTo(x+w-2*r, y+h-2*r, x+w, y+h,         startAng=0,   extent=90)
    p.lineTo(x+r, y+h)
    p.arcTo(x, y+h-2*r,       x+2*r, y+h,        startAng=90,  extent=90)
    p.lineTo(x, y+r)
    p.arcTo(x, y,              x+2*r, y+2*r,      startAng=180, extent=90)
    p.close()
    c.drawPath(p, fill=1 if fill else 0, stroke=1 if stroke else 0)

def qr_reader(data: str, px: int = 300) -> ImageReader:
    qr = qrcode.QRCode(border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img = img.resize((px, px))
    buf = BytesIO(); img.save(buf, "PNG"); buf.seek(0)
    return ImageReader(buf)


# ── Single mini-card ──────────────────────────────────────────
# Card size: 57mm x 75mm  (fits 3 columns x 3 rows on A4 with margins)
CW, CH   = 57*mm, 75*mm
CORNER   = 5
HDR_H    = 14*mm
QR_SIZE  = 26*mm
FOOT_H   = 6*mm

def draw_card(c, ox, oy, full_name, student_id, password):
    """Draw one student card. ox/oy = bottom-left corner of card."""

    # Card background
    rrect(c, ox, oy, CW, CH, CORNER, fill=WHITE, stroke=BORDER, lw=0.5)

    # ── Header ──────────────────────────────────────────────
    c.saveState()
    p = c.beginPath(); p.rect(ox, oy+CH-HDR_H, CW, HDR_H); c.clipPath(p, stroke=0)
    rrect(c, ox, oy+CH-HDR_H, CW, HDR_H, CORNER, fill=DARK)
    c.restoreState()

    # "IT SCHOOL" badge
    badge = "IT SCHOOL"
    c.setFont("Helvetica-Bold", 5)
    bw = c.stringWidth(badge, "Helvetica-Bold", 5) + 8
    rrect(c, ox+3*mm, oy+CH-5.5*mm, bw, 4*mm, 2, fill=ACCENT)
    sf(c, WHITE); c.setFont("Helvetica-Bold", 5)
    c.drawString(ox+5*mm, oy+CH-4.2*mm, badge)

    # Student name (two lines if space needed)
    parts = full_name.strip().split(" ", 1)
    sf(c, WHITE)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(ox+3*mm, oy+CH-9*mm, parts[0])
    if len(parts) == 2:
        c.setFont("Helvetica", 6.5)
        c.drawString(ox+3*mm, oy+CH-12.5*mm, parts[1])

    # ── QR code ─────────────────────────────────────────────
    qx = ox + (CW - QR_SIZE) / 2
    qy = oy + CH - HDR_H - QR_SIZE - 3*mm
    rrect(c, qx-1, qy-1, QR_SIZE+2, QR_SIZE+2, 3, fill=WHITE, stroke=BORDER, lw=0.5)
    qr_data = f"ID:{student_id}|PW:{password}"
    c.drawImage(qr_reader(qr_data), qx, qy, width=QR_SIZE, height=QR_SIZE,
                preserveAspectRatio=True, mask="auto")

    # ── Divider ─────────────────────────────────────────────
    div_y = qy - 3*mm
    ss(c, BORDER); c.setLineWidth(0.4)
    c.line(ox+3*mm, div_y, ox+CW-3*mm, div_y)

    # ── ID / Password cells ──────────────────────────────────
    cell_y  = div_y - 9*mm
    cell_h  = 8*mm
    pad     = 3*mm
    gap     = 2*mm
    cell_w  = (CW - pad*2 - gap) / 2

    for i, (lbl, val) in enumerate([("ID", str(student_id)), ("PASSWORD", str(password))]):
        cx = ox + pad + i*(cell_w+gap)
        rrect(c, cx, cell_y, cell_w, cell_h, 3, fill=LIGHT, stroke=BORDER, lw=0.4)
        sf(c, MUTED); c.setFont("Helvetica", 4.5)
        c.drawString(cx+2*mm, cell_y+cell_h-3*mm, lbl)
        sf(c, BLACK)
        # shrink font if value too wide
        fs = 7
        while c.stringWidth(str(val), "Courier-Bold", fs) > cell_w - 4*mm and fs > 4:
            fs -= 0.5
        c.setFont("Courier-Bold", fs)
        c.drawString(cx+2*mm, cell_y+2*mm, str(val))

    # ── Footer ───────────────────────────────────────────────
    c.saveState()
    p = c.beginPath(); p.rect(ox, oy, CW, FOOT_H); c.clipPath(p, stroke=0)
    rrect(c, ox, oy, CW, FOOT_H, CORNER, fill=LIGHT)
    c.restoreState()
    ss(c, BORDER); c.setLineWidth(0.4)
    c.line(ox, oy+FOOT_H, ox+CW, oy+FOOT_H)
    sf(c, MUTED); c.setFont("Helvetica", 4)
    c.drawString(ox+3*mm, oy+2*mm, "STUDENT CARD")
    # dots
    for di in range(3):
        sf(c, ACCENT if di == 0 else BORDER)
        c.circle(ox+CW-5*mm+di*3*mm, oy+3*mm, 1.2, fill=1, stroke=0)


# ── Group PDF ─────────────────────────────────────────────────
COLS     = 3
MARGIN_X = 12*mm
MARGIN_Y = 12*mm
GAP_X    = 5*mm
GAP_Y    = 5*mm
HEADER_AREA = 28*mm   # space at top for group title + teacher

def generate_group_pdf(
    group_name: str,
    teacher_name: str,
    students: list[dict],   # [{"full_name": ..., "student_id": ..., "password": ...}]
) -> bytes:
    buf = BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)

    def draw_page_header(page_num=1):
        """Group name + teacher at top of each page."""
        # Group name
        sf(c, BLACK); c.setFont("Helvetica-Bold", 16)
        title = group_name
        tw = c.stringWidth(title, "Helvetica-Bold", 16)
        c.drawString((PW-tw)/2, PH - 14*mm, title)

        # Teacher
        sf(c, MUTED); c.setFont("Helvetica", 10)
        sub = f"Teacher: {teacher_name}"
        sw = c.stringWidth(sub, "Helvetica", 10)
        c.drawString((PW-sw)/2, PH - 22*mm, sub)

        # Thin divider under header
        ss(c, BORDER); c.setLineWidth(0.5)
        c.line(MARGIN_X, PH - 26*mm, PW - MARGIN_X, PH - 26*mm)

    # Available width for cards
    avail_w = PW - MARGIN_X*2
    # card + gap total per column
    total_cw = (avail_w - GAP_X*(COLS-1)) / COLS   # should equal CW
    # rows per page (first page has header)
    avail_h_first = PH - MARGIN_Y - HEADER_AREA - MARGIN_Y
    avail_h_rest  = PH - MARGIN_Y*2
    rows_first = int(avail_h_first // (CH + GAP_Y))
    rows_rest  = int(avail_h_rest  // (CH + GAP_Y))

    cards_first_page = rows_first * COLS

    draw_page_header()

    for idx, stu in enumerate(students):
        # Determine position
        if idx < cards_first_page:
            local = idx
            row = local // COLS
            col = local % COLS
            ox = MARGIN_X + col*(CW + GAP_X)
            # top of cards area on first page
            top_y = PH - MARGIN_Y - HEADER_AREA
            oy = top_y - (row+1)*CH - row*GAP_Y
        else:
            local = idx - cards_first_page
            page  = local // (rows_rest * COLS)
            pos   = local % (rows_rest * COLS)
            row = pos // COLS
            col = pos % COLS

            if pos == 0:
                c.showPage()
                draw_page_header()

            ox = MARGIN_X + col*(CW + GAP_X)
            top_y = PH - MARGIN_Y - HEADER_AREA
            oy = top_y - (row+1)*CH - row*GAP_Y

        draw_card(
            c, ox, oy,
            full_name=stu["full_name"],
            student_id=stu["student_id"],
            password=stu["password"],
        )

    c.save()
    return buf.getvalue()
