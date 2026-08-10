import subprocess
import os
import base64
import unicodedata
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

def sanitize_text(text: str) -> str:
    """
    Remove characters that cannot be encoded in the default system encoding.
    Transliterates to ASCII where possible, replaces others with '?'.
    """
    # Normalize to NFKD to decompose accented characters
    normalized = unicodedata.normalize('NFKD', text)
    # Encode to ASCII, ignoring errors, then decode back
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
    # Replace any remaining non-ASCII (like \ufffd) with '?'
    return ascii_text.replace('\ufffd', '?')

def safe_draw_string(c, x, y, text, max_width=120):
    """Draw text safely, truncating and sanitizing each line."""
    safe_text = sanitize_text(text)[:max_width]
    try:
        c.drawString(x, y, safe_text)
    except UnicodeEncodeError:
        # Fallback: further strip non-ASCII
        c.drawString(x, y, safe_text.encode('ascii', 'ignore').decode('ascii'))

def render_mermaid_to_png(mermaid_code: str, output_path: str) -> bool:
    mmd_path = output_path + ".mmd"
    with open(mmd_path, "w", encoding='utf-8') as f:
        f.write(mermaid_code)
    try:
        subprocess.run([
            "mmdc", "-i", mmd_path, "-o", output_path, "-b", "white", "--scale", "2"
        ], check=True, capture_output=True)
        os.remove(mmd_path)
        return True
    except Exception:
        if os.path.exists(mmd_path):
            os.remove(mmd_path)
        return False

def generate_pdf_base64(report_text: str, mermaid_dict: dict) -> str:
    """Generates PDF and returns it as a base64 string."""
    pdf_path = "temp_output.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    y_position = height - 50
    c.setFont("Helvetica", 10)
    
    # Sanitize the full report text
    safe_report = sanitize_text(report_text)
    for line in safe_report.split('\n'):
        if y_position < 50:
            c.showPage()
            y_position = height - 50
            c.setFont("Helvetica", 10)
        safe_draw_string(c, 50, y_position, line)
        y_position -= 15
    
    for name, code in mermaid_dict.items():
        img_path = f"{name}.png"
        if render_mermaid_to_png(code, img_path) and os.path.exists(img_path):
            c.showPage()
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 50, f"Diagram: {name}")
            img = Image.open(img_path)
            w, h = img.size
            aspect = h / w
            draw_w = 450
            draw_h = draw_w * aspect
            if draw_h > 600:
                draw_h = 600
                draw_w = 600 / aspect
            c.drawImage(ImageReader(img_path), 50, height - draw_h - 100, 
                        width=draw_w, height=draw_h)
            os.remove(img_path)
        else:
            c.showPage()
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 50, f"Diagram: {name} (text fallback)")
            y = height - 100
            safe_code = sanitize_text(code)
            for line in safe_code.split('\n')[:15]:
                safe_draw_string(c, 50, y, line)
                y -= 15
    c.save()
    
    with open(pdf_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode("utf-8")
    os.remove(pdf_path)
    return pdf_data

def generate_txt(report_text: str, mermaid_dict: dict) -> str:
    txt = sanitize_text(report_text) + "\n\n--- MERMAID DIAGRAMS ---\n\n"
    for name, code in mermaid_dict.items():
        txt += f"### {name}\n```mermaid\n{sanitize_text(code)}\n```\n\n"
    return txt