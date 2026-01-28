import base64
import io
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageOps
except ImportError:  # pragma: no cover - entorno sin Pillow
    Image = ImageDraw = ImageOps = None

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image as RLImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    KeepInFrame,
    KeepTogether,
)
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# Configuración de la página
st.set_page_config(
    page_title="Generador de Entrenamientos CrossFit",
    page_icon="CF",
    layout="wide"
)

BASE_DIR = Path(__file__).parent
ICONO_PROFESOR = BASE_DIR / "iconoentrena.jpg"
ENCABEZADO_IMG = BASE_DIR / "encabezado.jpeg"
CC_LOGO_PATH = BASE_DIR / "cc.png"
EMOJI_FONT_PATH = Path("C:/Windows/Fonts/seguiemj.ttf")
EMOJI_FONT_REGULAR_NAME = "SegoeUIEmoji"
EMOJI_FONT_BOLD_NAME = "SegoeUIEmoji-Bold"
DEFAULT_FONT_REGULAR = "Helvetica"
DEFAULT_FONT_BOLD = "Helvetica-Bold"
PROFESOR_NOMBRE = "Profesor Víctor Manuel Marcos Muñoz"
PROFESOR_EMAIL = "victorm.marmun@educa.jcyl.es"


@lru_cache(maxsize=1)
def registrar_fuente_emoji() -> bool:
    if not EMOJI_FONT_PATH.exists():
        return False
    try:
        pdfmetrics.registerFont(TTFont(EMOJI_FONT_REGULAR_NAME, str(EMOJI_FONT_PATH)))
        pdfmetrics.registerFont(TTFont(EMOJI_FONT_BOLD_NAME, str(EMOJI_FONT_PATH)))
        return True
    except Exception:
        return False


def obtener_fuentes_para_pdf():
    if registrar_fuente_emoji():
        return EMOJI_FONT_REGULAR_NAME, EMOJI_FONT_BOLD_NAME
    return DEFAULT_FONT_REGULAR, DEFAULT_FONT_BOLD


@lru_cache(maxsize=1)
def obtener_icono_data_uri():
    if not ICONO_PROFESOR.exists():
        return None
    mime = "image/png" if ICONO_PROFESOR.suffix.lower() == ".png" else "image/jpeg"
    encoded = base64.b64encode(ICONO_PROFESOR.read_bytes()).decode()
    return f"data:{mime};base64,{encoded}"


@lru_cache(maxsize=1)
def obtener_icono_profesor_pdf_bytes():
    if not ICONO_PROFESOR.exists() or Image is None or ImageDraw is None or ImageOps is None:
        return None
    try:
        with Image.open(ICONO_PROFESOR) as img:
            side = 480
            square = ImageOps.fit(img.convert("RGBA"), (side, side))
            mask = Image.new("L", (side, side), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, side, side), fill=255)
            circular = Image.new("RGBA", (side, side), (255, 255, 255, 0))
            circular.paste(square, (0, 0), mask=mask)

            border_size = side + 48
            output_image = Image.new("RGBA", (border_size, border_size), (255, 255, 255, 0))
            ImageDraw.Draw(output_image).ellipse((0, 0, border_size, border_size), fill=(255, 255, 255, 255))
            output_image.paste(circular, (24, 24), mask=circular)
            ImageDraw.Draw(output_image).ellipse(
                (6, 6, border_size - 6, border_size - 6),
                outline=(255, 107, 107, 255),
                width=10,
            )

            buffer = io.BytesIO()
            output_image.save(buffer, format="PNG")
            return buffer.getvalue()
    except Exception:
        return None


@lru_cache(maxsize=8)
def generar_icono_decorativo(tipo: str):
    if Image is None or ImageDraw is None:
        return None

    size = 512
    img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    center = size / 2

    def rounded_rect(coords, radius, fill, outline=None, width=1):
        rounded = getattr(draw, "rounded_rectangle", None)
        if callable(rounded):
            rounded(coords, radius=radius, fill=fill, outline=outline, width=width)
        else:
            draw.rectangle(coords, fill=fill, outline=outline, width=width)

    def draw_target():
        palette = [
            ((255, 107, 107, 255), 0.48),
            ((255, 255, 255, 255), 0.32),
            ((78, 205, 196, 255), 0.19),
        ]
        for color, ratio in palette:
            radius = size * ratio
            draw.ellipse(
                (center - radius, center - radius, center + radius, center + radius),
                fill=color,
            )
        draw.ellipse(
            (center - size * 0.06, center - size * 0.06, center + size * 0.06, center + size * 0.06),
            fill=(26, 83, 92, 255),
        )

    def draw_strength():
        base_color = (244, 162, 97, 255)
        shade = (231, 111, 81, 255)
        highlight = (255, 224, 210, 255)
        draw.ellipse((0, 0, size, size), fill=(255, 255, 255, 60))
        draw.pieslice(
            (size * 0.02, size * 0.2, size * 0.98, size * 1.05),
            210,
            330,
            fill=base_color,
            outline=shade,
            width=10,
        )
        draw.ellipse(
            (size * 0.45, size * 0.05, size * 0.85, size * 0.42),
            fill=base_color,
            outline=shade,
            width=8,
        )
        draw.rectangle(
            (size * 0.58, size * 0.58, size * 0.92, size * 0.82),
            fill=shade,
        )
        draw.ellipse(
            (size * 0.82, size * 0.62, size * 1.02, size * 0.92),
            fill=shade,
        )
        draw.arc(
            (size * 0.18, size * 0.25, size * 0.88, size * 0.95),
            220,
            330,
            fill=highlight,
            width=6,
        )

    def draw_notes():
        bg_color = (255, 248, 224, 255)
        border_color = (244, 162, 97, 255)
        clip_color = (255, 107, 107, 255)
        rounded_rect(
            (size * 0.15, size * 0.15, size * 0.85, size * 0.9),
            radius=60,
            fill=bg_color,
            outline=border_color,
            width=8,
        )
        draw.rectangle(
            (size * 0.35, size * 0.05, size * 0.65, size * 0.2),
            fill=clip_color,
        )
        for idx, y in enumerate([0.3, 0.45, 0.6, 0.75]):
            draw.line(
                (size * 0.22, size * y, size * 0.78, size * y),
                fill=(80, 82, 92, 255),
                width=10,
            )
            draw.ellipse(
                (size * 0.22, size * y - 12, size * 0.24, size * y + 12),
                fill=(255, 214, 10, 255),
            )

    def draw_settings():
        track_color = (224, 232, 255, 255)
        knob_color = (78, 205, 196, 255)
        draw.ellipse((0, 0, size, size), fill=(247, 249, 255, 255))
        for idx, y in enumerate([0.35, 0.52, 0.69]):
            draw.line(
                (size * 0.2, size * y, size * 0.8, size * y),
                fill=track_color,
                width=28,
            )
            knob_x = 0.3 + idx * 0.2
            draw.ellipse(
                (size * knob_x, size * y - 40, size * (knob_x + 0.12), size * y + 40),
                fill=knob_color if idx % 2 == 0 else (255, 107, 107, 255),
                outline=(255, 255, 255, 255),
                width=6,
            )

    def draw_timer():
        body_color = (255, 238, 221, 255)
        ring = (255, 107, 107, 255)
        hand = (29, 53, 87, 255)
        draw.ellipse((size * 0.08, size * 0.12, size * 0.92, size * 0.96), fill=body_color, outline=ring, width=14)
        draw.rectangle((size * 0.38, 0, size * 0.62, size * 0.18), fill=ring)
        draw.rectangle((size * 0.25, size * 0.05, size * 0.38, size * 0.18), fill=(29, 53, 87, 255))
        draw.rectangle((size * 0.62, size * 0.05, size * 0.75, size * 0.18), fill=(29, 53, 87, 255))
        draw.ellipse((size * 0.32, size * 0.36, size * 0.68, size * 0.72), outline=ring, width=10)
        draw.line((center, size * 0.38, center, size * 0.62), fill=hand, width=16)
        draw.line((center, size * 0.38, size * 0.65, size * 0.3), fill=hand, width=16)

    def draw_movement():
        bg_color = (236, 253, 245, 255)
        accent = (16, 185, 129, 255)
        secondary = (5, 150, 105, 255)
        draw.ellipse((0, 0, size, size), fill=bg_color)
        draw.arc((size * 0.2, size * 0.2, size * 0.9, size * 0.9), 200, 320, fill=accent, width=18)
        draw.ellipse((size * 0.52, size * 0.18, size * 0.7, size * 0.36), fill=secondary)
        draw.line((size * 0.6, size * 0.34, size * 0.48, size * 0.55), fill=secondary, width=30)
        draw.line((size * 0.48, size * 0.55, size * 0.66, size * 0.72), fill=accent, width=28)
        draw.line((size * 0.52, size * 0.45, size * 0.66, size * 0.52), fill=accent, width=26)
        draw.line((size * 0.52, size * 0.45, size * 0.4, size * 0.3), fill=accent, width=20)

    def draw_performance():
        base = (255, 251, 235, 255)
        ribbon = (249, 115, 22, 255)
        medal = (247, 224, 138, 255)
        star = (251, 191, 36, 255)
        draw.ellipse((0, 0, size, size), fill=base)
        draw.polygon(
            [
                (size * 0.4, size * 0.05),
                (size * 0.5, size * 0.28),
                (size * 0.6, size * 0.05),
                (size * 0.74, size * 0.05),
                (size * 0.55, size * 0.45),
                (size * 0.45, size * 0.45),
                (size * 0.26, size * 0.05),
            ],
            fill=ribbon,
        )
        draw.ellipse((size * 0.25, size * 0.32, size * 0.75, size * 0.82), fill=medal, outline=ribbon, width=12)
        draw.polygon(
            [
                (center, size * 0.38),
                (size * 0.43, size * 0.58),
                (size * 0.28, size * 0.6),
                (size * 0.4, size * 0.72),
                (size * 0.36, size * 0.88),
                (center, size * 0.8),
                (size * 0.64, size * 0.88),
                (size * 0.6, size * 0.72),
                (size * 0.72, size * 0.6),
                (size * 0.57, size * 0.58),
            ],
            fill=star,
        )

    def draw_wellbeing():
        base = (237, 233, 254, 255)
        heart = (244, 114, 182, 255)
        brain = (99, 102, 241, 255)
        draw.ellipse((0, 0, size, size), fill=base)
        draw.ellipse((size * 0.22, size * 0.3, size * 0.48, size * 0.62), fill=brain)
        draw.ellipse((size * 0.38, size * 0.32, size * 0.64, size * 0.64), fill=brain)
        draw.rectangle((size * 0.38, size * 0.45, size * 0.64, size * 0.65), fill=brain)
        draw.arc((size * 0.2, size * 0.5, size * 0.8, size * 0.9), 200, 340, fill=(165, 180, 252, 255), width=18)
        heart_points = [
            (size * 0.5, size * 0.8),
            (size * 0.32, size * 0.62),
            (size * 0.32, size * 0.48),
            (size * 0.42, size * 0.4),
            (size * 0.5, size * 0.48),
            (size * 0.58, size * 0.4),
            (size * 0.68, size * 0.48),
            (size * 0.68, size * 0.62),
        ]
        draw.polygon(heart_points, fill=heart)

    def draw_dumbbell():
        bg = (249, 250, 255, 255)
        plate = (31, 41, 55, 255)
        plate_inner = (75, 85, 99, 255)
        handle = (209, 213, 219, 255)
        grip = (156, 163, 175, 255)
        accent = (249, 115, 22, 255)
        draw.ellipse((0, 0, size, size), fill=bg)
        # left plates
        rounded_rect((size * 0.12, size * 0.3, size * 0.24, size * 0.7), radius=60, fill=plate)
        rounded_rect((size * 0.16, size * 0.34, size * 0.28, size * 0.66), radius=50, fill=plate_inner)
        rounded_rect((size * 0.2, size * 0.38, size * 0.3, size * 0.62), radius=40, fill=accent)
        # right plates
        rounded_rect((size * 0.76, size * 0.3, size * 0.88, size * 0.7), radius=60, fill=plate)
        rounded_rect((size * 0.72, size * 0.34, size * 0.84, size * 0.66), radius=50, fill=plate_inner)
        rounded_rect((size * 0.7, size * 0.38, size * 0.8, size * 0.62), radius=40, fill=accent)
        # handle
        draw.rectangle((size * 0.28, size * 0.45, size * 0.72, size * 0.55), fill=handle)
        draw.rectangle((size * 0.33, size * 0.45, size * 0.67, size * 0.55), fill=grip)
        for idx in range(5):
            x = size * (0.34 + idx * 0.07)
            draw.line((x, size * 0.45, x, size * 0.55), fill=handle, width=6)

    def draw_lifter():
        bg = (255, 247, 237, 255)
        body = (251, 146, 60, 255)
        bar = (31, 41, 55, 255)
        plates = (59, 130, 246, 255)
        draw.ellipse((0, 0, size, size), fill=bg)
        draw.line((size * 0.2, size * 0.28, size * 0.8, size * 0.28), fill=bar, width=24)
        draw.rectangle((size * 0.18, size * 0.16, size * 0.24, size * 0.4), fill=plates)
        draw.rectangle((size * 0.76, size * 0.16, size * 0.82, size * 0.4), fill=plates)
        draw.ellipse((center - size * 0.08, size * 0.32, center + size * 0.08, size * 0.48), fill=body)
        draw.line((center, size * 0.48, size * 0.74, size * 0.68), fill=body, width=26)
        draw.line((center, size * 0.48, size * 0.26, size * 0.68), fill=body, width=26)
        draw.line((size * 0.62, size * 0.84, size * 0.5, size * 0.62), fill=body, width=24)
        draw.line((size * 0.38, size * 0.84, size * 0.5, size * 0.62), fill=body, width=24)
        draw.ellipse((center - size * 0.07, size * 0.18, center + size * 0.07, size * 0.32), fill=(254, 215, 170, 255))
        draw.arc((center - size * 0.05, size * 0.24, center + size * 0.05, size * 0.34), 200, -20, fill=bar, width=6)

    def draw_summit():
        sky = (224, 242, 255, 255)
        mountain = (71, 85, 105, 255)
        snow = (226, 232, 240, 255)
        flagpole = (30, 41, 59, 255)
        flag = (250, 82, 82, 255)
        sun = (252, 211, 77, 255)
        draw.ellipse((0, 0, size, size), fill=sky)
        draw.ellipse((size * 0.68, size * 0.08, size * 0.9, size * 0.3), fill=sun)
        draw.polygon(
            [
                (size * 0.15, size * 0.9),
                (size * 0.38, size * 0.52),
                (size * 0.52, size * 0.66),
                (size * 0.68, size * 0.4),
                (size * 0.88, size * 0.9),
            ],
            fill=mountain,
        )
        draw.polygon(
            [
                (size * 0.56, size * 0.45),
                (size * 0.64, size * 0.32),
                (size * 0.72, size * 0.52),
            ],
            fill=snow,
        )
        draw.rectangle((size * 0.64, size * 0.25, size * 0.66, size * 0.58), fill=flagpole)
        draw.polygon(
            [
                (size * 0.66, size * 0.26),
                (size * 0.82, size * 0.32),
                (size * 0.66, size * 0.38),
            ],
            fill=flag,
        )

    def draw_creative_commons():
        bg = (244, 247, 252, 255)
        ring = (31, 41, 55, 255)
        text_color = (31, 41, 55, 255)
        accent = (255, 255, 255, 255)
        draw.ellipse((0, 0, size, size), fill=bg)
        draw.ellipse((size * 0.08, size * 0.08, size * 0.92, size * 0.92), outline=ring, width=28)
        draw.ellipse((size * 0.18, size * 0.18, size * 0.82, size * 0.82), fill=ring)
        draw.ellipse((size * 0.23, size * 0.23, size * 0.77, size * 0.77), fill=accent)
        draw.ellipse((size * 0.32, size * 0.36, size * 0.45, size * 0.64), outline=ring, width=14)
        draw.ellipse((size * 0.55, size * 0.36, size * 0.68, size * 0.64), outline=ring, width=14)
        draw.arc((size * 0.26, size * 0.36, size * 0.74, size * 0.78), 210, 330, fill=ring, width=16)
        draw.text((size * 0.37, size * 0.18), "CC", fill=text_color)

    draw_funcs = {
        "target": draw_target,
        "strength": draw_strength,
        "notes": draw_notes,
        "settings": draw_settings,
        "timer": draw_timer,
        "movement": draw_movement,
        "performance": draw_performance,
        "wellbeing": draw_wellbeing,
        "dumbbell": draw_dumbbell,
        "lifter": draw_lifter,
        "summit": draw_summit,
        "creative_commons": draw_creative_commons,
    }

    painter = draw_funcs.get(tipo)
    if painter is None:
        return None

    painter()
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@lru_cache(maxsize=1)
def obtener_logo_creative_commons():
    if CC_LOGO_PATH.exists():
        try:
            return CC_LOGO_PATH.read_bytes()
        except Exception:
            pass
    return generar_icono_decorativo('creative_commons')

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #FF6B6B;
        text-align: center;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #4ECDC4;
        margin-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<p class="main-header">💪Generador de Entrenamientos de CrossFit💪</p>', unsafe_allow_html=True)

icono_data_uri = obtener_icono_data_uri()
if icono_data_uri:
    st.markdown(
        f"""
        <div style='display:flex; align-items:center; justify-content:center; gap:0.8rem; margin-bottom:1rem;'>
            <img src="{icono_data_uri}" alt="Profesor" style="width:68px; height:68px; border-radius:50%; object-fit:cover; box-shadow:0 0 12px rgba(0,0,0,0.15);" />
            <span style='font-size:1.2rem; font-weight:600; color:#2C3E50;'>
                {PROFESOR_NOMBRE} · <a href="mailto:{PROFESOR_EMAIL}" style="color:#0EA5E9; text-decoration:none;">{PROFESOR_EMAIL}</a>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(f"### {PROFESOR_NOMBRE} · {PROFESOR_EMAIL}")

if "visitas_registradas" not in st.session_state:
    st.session_state["visitas_registradas"] = False
if "visit_counter" not in st.session_state:
    st.session_state["visit_counter"] = 0
if not st.session_state["visitas_registradas"]:
    st.session_state["visit_counter"] += 1
    st.session_state["visitas_registradas"] = True
st.session_state.setdefault("descargas_pdf", 0)
if st.session_state.pop("registrar_descarga", False):
    st.session_state["descargas_pdf"] += 1

st.info(
    """
    El CrossFit combina movimientos funcionales ejecutados a alta intensidad en formato circuito para
    desarrollar fuerza, resistencia y coordinación. Cada entrenamiento debe adaptarse a las características
    personales y al material disponible, priorizando la seguridad en todo momento.

    - Utiliza cargas moderadas que no comprometan la técnica ni supongan riesgo de lesión.
    - Si el circuito requiere muchas repeticiones, opta por ejercicios de autocarga o con cargas bajas.
    - Ajusta la selección de ejercicios y descansos según tu nivel y consulta con el profesor ante cualquier duda.
    
    ¡Recuerda que el objetivo es disfrutar del proceso y progresar de forma segura!
    """
)

col_visitas, col_descargas = st.columns(2)
col_visitas.metric("Visitas registradas", st.session_state["visit_counter"])
col_descargas.metric("Descargas de PDF", st.session_state["descargas_pdf"])

# Definición de ejercicios por categoría
EJERCICIOS = {
    "Autocarga": [
        "Flexiones (Push-ups)",
        "Sentadillas (Air Squats)",
        "Burpees",
        "Jumping Jacks",
        "Mountain Climbers",
        "Plank Hold",
        "Lunges (Zancadas)",
        "Jump Squats",
        "Pistol Squats",
        "Pull-ups (Dominadas)",
        "Dips",
        "Hollow Rock",
        "V-ups",
        "Superman Hold",
    ],
    "Barra Olímpica": [
        "Back Squat",
        "Front Squat",
        "Deadlift (Peso Muerto)",
        "Clean (Cargada)",
        "Snatch (Arrancada)",
        "Press de Hombro",
        "Push Press",
        "Thruster",
        "Overhead Squat",
        "Bench Press",
        "Barbell Row",
    ],
    "Mancuernas": [
        "Dumbbell Snatch",
        "Dumbbell Clean",
        "Dumbbell Press",
        "Goblet Squat",
        "Dumbbell Lunges",
        "Devil Press",
        "Dumbbell Thruster",
        "Renegade Rows",
        "Dumbbell Swing",
        "Farmers Walk",
    ],
    "Kettlebell": [
        "Kettlebell Swing",
        "Kettlebell Clean",
        "Kettlebell Snatch",
        "Turkish Get-up",
        "Goblet Squat",
        "Kettlebell Press",
        "Kettlebell Halo",
        "Russian Twist",
        "Single Arm Swing",
    ],
    "TRX": [
        "TRX Rows",
        "TRX Push-ups",
        "TRX Squat",
        "TRX Pike",
        "TRX Mountain Climbers",
        "TRX Fallout",
        "TRX Hamstring Curl",
        "TRX Atomic Push-up",
    ],
    "Cajón": [
        "Box Jump",
        "Box Step-up",
        "Jump Over",
        "Box Squat",
        "Decline Push-ups",
        "Bulgarian Split Squat",
    ],
    "Medball": [
        "Wall Ball",
        "Medicine Ball Slam",
        "Medicine Ball Clean",
        "Russian Twist con Medball",
        "Medicine Ball Sit-up",
        "Over the Shoulder Toss",
        "Medicine Ball Burpee",
    ],
    "Comba": [
        "Unders",
        "Under Crossover",
        "Double Under",
    ],
    "Carrera": [
        "Shuttle Run",
        "Carrera 100 m",
        "Carrera 200 m",
        "Carrera 400 m",
        "Carrera 600 m",
        "Carrera 800 m",
        "Carrera 1 km",
    ],
}

CARRERA_WODS_PERMITIDOS = {"AMRAP", "EMOM", "AFAP"}
EMOM_CARRERA_OPCIONES = {"Shuttle Run", "Carrera 100 m", "Carrera 200 m", "Carrera 400 m"}


def obtener_categorias_por_tipo(tipo_circuito: str):
    categorias = []
    for categoria, ejercicios in EJERCICIOS.items():
        lista = ejercicios
        if categoria == "Carrera":
            if tipo_circuito not in CARRERA_WODS_PERMITIDOS:
                continue
            if tipo_circuito == "EMOM":
                lista = [ej for ej in ejercicios if ej in EMOM_CARRERA_OPCIONES]
                if not lista:
                    continue
        categorias.append((categoria, lista))
    return categorias
# Información de tipos de circuito
TIPOS_CIRCUITO = {
    "AMRAP": {
        "nombre": "AMRAP (As Many Rounds As Possible)",
        "descripcion": "Completa tantas rondas como sea posible en el tiempo establecido",
        "duracion_sugerida": "10-20 minutos"
    },
    "EMOM": {
        "nombre": "EMOM (Every Minute On the Minute)",
        "descripcion": "Cada minuto comienza una nueva serie de ejercicios",
        "duracion_sugerida": "10-20 minutos"
    },
    "Tabata": {
        "nombre": "Tabata",
        "descripcion": "20 segundos de trabajo intenso, 10 segundos de descanso, repetir 8 veces",
        "duracion_sugerida": "4 minutos por ejercicio"
    },
    "Ladder": {
        "nombre": "Ladder (Escalera)",
        "descripcion": "Incrementa o disminuye las repeticiones en cada ronda",
        "duracion_sugerida": "Variable según repeticiones"
    },
    "AFAP": {
        "nombre": "AFAP (As Fast As Possible)",
        "descripcion": "Completa las repeticiones establecidas lo más rápido posible",
        "duracion_sugerida": "Variable"
    },
    "Circuito de Entrenamiento": {
        "nombre": "Circuito de Entrenamiento",
        "descripcion": "Secuencia de 6 a 12 ejercicios personalizados para objetivos de fuerza",
        "duracion_sugerida": "Variable según objetivo"
    }
}

OBJETIVOS_ENTRENAMIENTO = {
    "Fuerza Máxima": {
        "descripcion": "Prioriza la producción de fuerza absoluta con pocas repeticiones y descansos amplios.",
        "porcentaje": "85–100%",
        "carga": "85–100% del 1RM",
        "reps": "1–5",
        "series": "3–6",
        "descanso": "3–5 min",
        "rir": "2–4",
    },
    "Hipertrofia": {
        "descripcion": "Busca aumentar el tamaño muscular con un volumen moderado-alto y descansos controlados.",
        "porcentaje": "65–85%",
        "carga": "65–85% del 1RM",
        "reps": "6–12 (hasta 15)",
        "series": "3–5",
        "descanso": "60–90 s",
        "rir": "0–2",
    },
    "Fuerza-Resistencia": {
        "descripcion": "Mejora la capacidad de sostener esfuerzos prolongados con cargas ligeras y muchas repeticiones.",
        "porcentaje": "30–60%",
        "carga": "30–60% del 1RM",
        "reps": "15–30+",
        "series": "2–4",
        "descanso": "30–60 s",
        "rir": "3–5",
    },
}

OBJETIVOS_ORDEN = ["Fuerza Máxima", "Hipertrofia", "Fuerza-Resistencia"]
MIN_EJERCICIOS_CIRCUITO = 6
MAX_EJERCICIOS_CIRCUITO = 12
CIRCUITO_ENTRENAMIENTO_KEY = "Circuito de Entrenamiento"
EMOM_RECUPERACION_TEXTO = "El tiempo sobrante al terminar las repeticiones indicadas en cada ejercicio"

BORG_ESCALA = [
    {
        "nivel": "Muy ligero",
        "color": "#DCFCE7",
        "descripcion": "Respiración tranquila; sirve como calentamiento o descarga.",
    },
    {
        "nivel": "Ligero",
        "color": "#BBF7D0",
        "descripcion": "Puedes mantener una conversación corta; sensación cómoda.",
    },
    {
        "nivel": "Moderado",
        "color": "#FDE68A",
        "descripcion": "Empiezas a sudar; concentración total en la técnica.",
    },
    {
        "nivel": "Duro",
        "color": "#FECACA",
        "descripcion": "Respiración intensa; requiere pausas planificadas.",
    },
    {
        "nivel": "Muy duro",
        "color": "#FCA5A5",
        "descripcion": "Esfuerzo máximo sostenible sólo durante poco tiempo.",
    },
]

BENEFICIOS_WOD = {
    "AMRAP": [
        "Mejora la resistencia muscular al repetir rondas sostenidas.",
        "Potencia la capacidad de gestión del ritmo y del tiempo de trabajo.",
        "Favorece el uso de cargas moderadas con densidad alta de ejercicio.",
    ],
    "EMOM": [
        "Entrena la velocidad de ejecución bajo fatiga controlada.",
        "Refuerza la técnica mediante descansos breves y predecibles.",
        "Optimiza la autogestión del esfuerzo gracias a intervalos fijos.",
    ],
    "Tabata": [
        "Impulsa la potencia anaeróbica con intervalos explosivos.",
        "Incrementa la tolerancia al lactato en trabajos muy intensos.",
        "Favorece la quema calórica en tiempos reducidos.",
    ],
    "Ladder": [
        "Desarrolla fuerza progresiva gracias al aumento o disminución de repeticiones.",
        "Promueve el control de la técnica bajo volúmenes cambiantes.",
        "Estimula la concentración al gestionar saltos de carga o repeticiones.",
    ],
    "AFAP": [
        "Mejora la potencia y la velocidad de finalización de tareas.",
        "Incrementa la capacidad de mantener intensidad alta sin pausas largas.",
        "Entrena la toma de decisiones rápida bajo presión.",
    ],
    CIRCUITO_ENTRENAMIENTO_KEY: [
        "Permite atacar objetivos concretos de fuerza, hipertrofia o resistencia.",
        "Desarrolla equilibrio muscular combinando implementos y autocargas.",
        "Favorece la transferencia a gestos deportivos y de la vida diaria.",
    ],
}

BENEFICIOS_OTROS = [
    "Reduce el estrés y mejora el estado de ánimo a través de la liberación de endorfinas.",
    "Potencia la función cognitiva, la memoria de trabajo y la capacidad de concentración.",
    "Refuerza la autoconfianza y la percepción de autoeficacia en el entrenamiento diario.",
    "Mejora la calidad del sueño y acelera la recuperación mental.",
    "Favorece la socialización y el sentido de comunidad con el grupo de entrenamiento.",
    "Ayuda a regular la ansiedad y promueve hábitos saludables sostenibles.",
]


def extraer_rango_numerico(texto: Optional[str], fallback_min: int = 1, fallback_max: int = 10):
    """Obtiene el rango numérico (mínimo, máximo) presente en un texto como "6–12"."""
    if fallback_min > fallback_max:
        fallback_max = fallback_min
    numeros = [int(valor) for valor in re.findall(r"\d+", texto or "")]
    if not numeros:
        return fallback_min, fallback_max
    return min(numeros), max(numeros)


def valor_intermedio(min_val: int, max_val: int) -> int:
    """Devuelve un valor entero centrado dentro del rango dado."""
    if min_val >= max_val:
        return min_val
    return min_val + (max_val - min_val) // 2

EJERCICIOS_INFO = {
    "Flexiones (Push-ups)": ["Pectoral", "Tríceps", "Core"],
    "Sentadillas (Air Squats)": ["Cuádriceps", "Glúteos", "Core"],
    "Burpees": ["Cuerpo completo", "Cardio"],
    "Jumping Jacks": ["Hombros", "Piernas", "Cardio"],
    "Mountain Climbers": ["Core", "Hombros", "Cardio"],
    "Plank Hold": ["Core", "Hombros", "Lumbar"],
    "Lunges (Zancadas)": ["Cuádriceps", "Glúteos", "Isquiotibiales"],
    "Jump Squats": ["Cuádriceps", "Glúteos", "Sóleo y gemelos"],
    "Pistol Squats": ["Cuádriceps", "Glúteos", "Estabilidad"],
    "Pull-ups (Dominadas)": ["Espalda", "Bíceps", "Core"],
    "Dips": ["Tríceps", "Pectoral", "Hombros"],
    "Hollow Rock": ["Core", "Flexores de cadera"],
    "V-ups": ["Core", "Flexores de cadera"],
    "Superman Hold": ["Espalda baja", "Glúteos", "Isquiotibiales"],
    "Back Squat": ["Cuádriceps", "Glúteos", "Core"],
    "Front Squat": ["Cuádriceps", "Core", "Glúteos"],
    "Deadlift (Peso Muerto)": ["Espalda baja", "Isquiotibiales", "Glúteos"],
    "Clean (Cargada)": ["Glúteos", "Trapecio", "Cardio"],
    "Snatch (Arrancada)": ["Deltoides", "Glúteos", "Cuerpo completo"],
    "Press de Hombro": ["Deltoides", "Tríceps", "Core"],
    "Push Press": ["Hombros", "Piernas", "Tríceps"],
    "Thruster": ["Cuádriceps", "Hombros", "Cardio"],
    "Overhead Squat": ["Cuádriceps", "Hombros", "Core"],
    "Bench Press": ["Pectoral", "Tríceps", "Hombros"],
    "Barbell Row": ["Espalda media", "Bíceps", "Core"],
    "Dumbbell Snatch": ["Hombros", "Glúteos", "Cardio"],
    "Dumbbell Clean": ["Glúteos", "Espalda", "Brazos"],
    "Dumbbell Press": ["Hombros", "Tríceps", "Core"],
    "Goblet Squat": ["Cuádriceps", "Glúteos", "Core"],
    "Dumbbell Lunges": ["Cuádriceps", "Glúteos", "Estabilidad"],
    "Devil Press": ["Hombros", "Pectoral", "Cardio"],
    "Dumbbell Thruster": ["Cuádriceps", "Hombros", "Tríceps"],
    "Renegade Rows": ["Espalda", "Core", "Bíceps"],
    "Dumbbell Swing": ["Glúteos", "Hombros", "Core"],
    "Farmers Walk": ["Antebrazos", "Trapecio", "Core"],
    "Kettlebell Swing": ["Glúteos", "Isquiotibiales", "Core"],
    "Kettlebell Clean": ["Glúteos", "Espalda", "Brazos"],
    "Kettlebell Snatch": ["Deltoides", "Glúteos", "Cardio"],
    "Turkish Get-up": ["Hombros", "Core", "Estabilidad"],
    "Kettlebell Press": ["Hombros", "Tríceps", "Core"],
    "Kettlebell Halo": ["Hombros", "Core", "Trapecio"],
    "Russian Twist": ["Oblicuos", "Core", "Flexores de cadera"],
    "Single Arm Swing": ["Glúteos", "Core", "Hombros"],
    "TRX Rows": ["Espalda", "Bíceps", "Core"],
    "TRX Push-ups": ["Pectoral", "Tríceps", "Core"],
    "TRX Squat": ["Cuádriceps", "Glúteos", "Core"],
    "TRX Pike": ["Core", "Hombros", "Flexores de cadera"],
    "TRX Mountain Climbers": ["Core", "Cardio", "Hombros"],
    "TRX Fallout": ["Hombros", "Core", "Tríceps"],
    "TRX Hamstring Curl": ["Isquiotibiales", "Glúteos", "Core"],
    "TRX Atomic Push-up": ["Pectoral", "Core", "Hombros"],
    "Box Jump": ["Glúteos", "Cuádriceps", "Cardio"],
    "Box Step-up": ["Glúteos", "Cuádriceps", "Equilibrio"],
    "Jump Over": ["Cardio", "Glúteos", "Core"],
    "Box Squat": ["Cuádriceps", "Glúteos", "Core"],
    "Decline Push-ups": ["Pectoral superior", "Tríceps", "Hombros"],
    "Bulgarian Split Squat": ["Cuádriceps", "Glúteos", "Estabilidad"],
    "Wall Ball": ["Cuádriceps", "Hombros", "Cardio"],
    "Medicine Ball Slam": ["Espalda", "Abdomen", "Hombros"],
    "Medicine Ball Clean": ["Glúteos", "Espalda", "Brazos"],
    "Russian Twist con Medball": ["Oblicuos", "Core", "Flexores de cadera"],
    "Medicine Ball Sit-up": ["Abdomen", "Oblicuos"],
    "Over the Shoulder Toss": ["Espalda", "Glúteos", "Core"],
    "Medicine Ball Burpee": ["Cardio", "Hombros", "Piernas"],
    "Unders": ["Cardio", "Sóleo y gemelos", "Hombros"],
    "Under Crossover": ["Cardio", "Sóleo y gemelos", "Hombros"],
    "Double Under": ["Cardio", "Sóleo y gemelos", "Hombros"],
    "Shuttle Run": ["Cardio", "Cuádriceps", "Isquiotibiales"],
    "Carrera 100 m": ["Cardio", "Cuádriceps", "Sóleo y gemelos"],
    "Carrera 200 m": ["Cardio", "Cuádriceps", "Sóleo y gemelos"],
    "Carrera 400 m": ["Cardio", "Cuádriceps", "Sóleo y gemelos"],
    "Carrera 600 m": ["Cardio", "Cuádriceps", "Sóleo y gemelos"],
    "Carrera 800 m": ["Cardio", "Cuádriceps", "Sóleo y gemelos"],
    "Carrera 1 km": ["Cardio", "Cuádriceps", "Sóleo y gemelos"],
}
def obtener_musculos(ejercicio: str):
    return EJERCICIOS_INFO.get(ejercicio, ["Cuerpo completo"])


def construir_tabata_plan(ejercicios):
    if not ejercicios:
        return []
    bloques_totales = 8
    cantidad = len(ejercicios)
    base = bloques_totales // cantidad
    resto = bloques_totales % cantidad
    plan = []
    for idx, ejercicio in enumerate(ejercicios):
        bloques = base + (1 if idx < resto else 0)
        plan.append({
            "nombre": ejercicio["nombre"],
            "bloques": bloques
        })
    return plan

# Sidebar - Información del alumno
with st.sidebar:
    st.header("📋 Información del Alumno")
    nombre = st.text_input("Nombre completo:", placeholder="Ej: Sofía González")
    grupo = st.text_input("Grupo:", placeholder="Ej: 3°A")
    
    st.markdown("---")
    st.markdown("### 📖 Instrucciones")
    st.markdown("""
    1. Completa tu información
    2. Selecciona el WOD
    3. Elige tus ejercicios favoritos
    4. Ajusta parámetros
    5. ¡Descarga tu entrenamiento!
    """)

# Sección principal - Selección de tipo de circuito
st.markdown('<p class="sub-header">WOD</p>', unsafe_allow_html=True)
tipo_circuito = st.selectbox(
    "Selecciona el WOD:",
    options=list(TIPOS_CIRCUITO.keys()),
    format_func=lambda x: TIPOS_CIRCUITO[x]["nombre"]
)

# Mostrar información del circuito seleccionado
col1, col2 = st.columns(2)
with col1:
    st.info(f"**Descripción:** {TIPOS_CIRCUITO[tipo_circuito]['descripcion']}")
with col2:
    st.info(f"**Duración sugerida:** {TIPOS_CIRCUITO[tipo_circuito]['duracion_sugerida']}")

es_circuito_entrenamiento = tipo_circuito == CIRCUITO_ENTRENAMIENTO_KEY
objetivo = None
objetivo_info = {}
series_min = series_max = None
reps_min = reps_max = None
if es_circuito_entrenamiento:
    st.markdown('<p class="sub-header">Objetivo del Entrenamiento</p>', unsafe_allow_html=True)
    objetivo = st.radio(
        "Selecciona el objetivo principal:",
        options=OBJETIVOS_ORDEN,
        index=1,
        horizontal=True,
    )
    objetivo_info = OBJETIVOS_ENTRENAMIENTO.get(objetivo, {})
    st.caption(objetivo_info.get("descripcion", ""))
    if objetivo_info:
        series_min, series_max = extraer_rango_numerico(objetivo_info.get("series"), 3, 6)
        reps_min, reps_max = extraer_rango_numerico(objetivo_info.get("reps"), 8, 15)
        st.markdown("**Parámetros del objetivo:**")
        parametros_objetivo = [
            ("Carga", objetivo_info.get("carga", "-")),
            ("Reps", objetivo_info.get("reps", "-")),
            ("Series", objetivo_info.get("series", "-")),
            ("Descanso", objetivo_info.get("descanso", "-")),
            ("RIR", objetivo_info.get("rir", "-")),
        ]
        cols_param = st.columns(len(parametros_objetivo))
        for col, (label, value) in zip(cols_param, parametros_objetivo):
            col.markdown(f"<small>{label}</small><br/><strong>{value}</strong>", unsafe_allow_html=True)

# Parámetros del WOD
st.markdown('<p class="sub-header">Parámetros del WOD</p>', unsafe_allow_html=True)

duracion = None
numero_rondas = None
numero_ejercicios_tabata = None
incremento = None
reps_inicio = None
ladder_direccion = "Creciente"

param_col1, param_col2, param_col3 = st.columns(3)

with param_col1:
    if tipo_circuito in ["AMRAP", "EMOM"]:
        duracion = st.number_input("Duración (minutos):", min_value=5, max_value=60, value=15)
    elif tipo_circuito == "Tabata":
        numero_ejercicios_tabata = st.selectbox(
            "Número de ejercicios (1, 2, 4 u 8):",
            options=[1, 2, 4, 8],
            index=2,
        )
    else:
        if es_circuito_entrenamiento and series_min is not None and series_max is not None:
            valor_series = valor_intermedio(series_min, series_max)
            numero_rondas = st.number_input(
                "Número de rondas:",
                min_value=series_min,
                max_value=series_max,
                value=valor_series,
            )
            st.caption(f"Rango objetivo: {series_min}-{series_max} series")
        else:
            numero_rondas = st.number_input("Número de rondas:", min_value=1, max_value=10, value=3)

with param_col2:
    if tipo_circuito == "Ladder":
        incremento = st.number_input("Cambio de repeticiones por ronda:", min_value=1, max_value=10, value=2)
        reps_inicio = st.number_input("Repeticiones iniciales:", min_value=1, max_value=50, value=5)

with param_col3:
    if tipo_circuito == "Ladder":
        ladder_direccion = st.selectbox("Dirección de progresión:", ["Creciente", "Decreciente"])

# Selección de ejercicios
st.markdown('<p class="sub-header">Selección de Ejercicios</p>', unsafe_allow_html=True)

ejercicios_seleccionados = []
ejercicios_para_descarga = []
plan_tabata = None
tabata_listo = True
ejercicios_validos = True

# Crear tabs para cada categoría
categorias_disponibles = obtener_categorias_por_tipo(tipo_circuito)

if not categorias_disponibles:
    st.warning("No hay categorías de ejercicios disponibles para este WOD.")
else:
    tabs = st.tabs([categoria for categoria, _ in categorias_disponibles])

    for idx, (categoria, ejercicios) in enumerate(categorias_disponibles):
        with tabs[idx]:
            st.markdown(f"**Ejercicios de {categoria}**")
            cols = st.columns(2)
            for i, ejercicio in enumerate(ejercicios):
                with cols[i % 2]:
                    st.markdown(f"**{ejercicio}**")
                    st.caption(f"Grupos musculares: {', '.join(obtener_musculos(ejercicio))}")
                    seleccionado = st.checkbox(f"Incluir {ejercicio}", key=f"{categoria}_{ejercicio}")
                    if seleccionado:
                        repeticiones = None
                        if tipo_circuito not in ["Tabata", "Ladder"]:
                            if ejercicio == "Shuttle Run":
                                opciones_base = [4, 6, 10, 12, 14, 16, 20]
                                opciones = opciones_base
                                indice_default = min(2, len(opciones) - 1)
                                if es_circuito_entrenamiento and reps_min is not None and reps_max is not None:
                                    opciones_filtradas = [opt for opt in opciones_base if reps_min <= opt <= reps_max]
                                    if not opciones_filtradas:
                                        opciones_filtradas = sorted({reps_min, reps_max})
                                    opciones = sorted(opciones_filtradas)
                                    objetivo_reps = valor_intermedio(reps_min, reps_max)
                                    valor_default = min(opciones, key=lambda val: abs(val - objetivo_reps))
                                    indice_default = opciones.index(valor_default)
                                repeticiones = st.selectbox(
                                    f"Repeticiones para {ejercicio}",
                                    options=opciones,
                                    index=indice_default,
                                    key=f"reps_{categoria}_{ejercicio}",
                                )
                            elif ejercicio == "Plank Hold":
                                segundos = st.number_input(
                                    f"Tiempo (segundos) para {ejercicio}",
                                    min_value=10,
                                    max_value=300,
                                    value=30,
                                    step=5,
                                    key=f"segundos_{categoria}_{ejercicio}",
                                )
                                repeticiones = f"{int(segundos)} s"
                            else:
                                if es_circuito_entrenamiento and reps_min is not None and reps_max is not None:
                                    default_reps = valor_intermedio(reps_min, reps_max)
                                    repeticiones = st.number_input(
                                        f"Repeticiones para {ejercicio}",
                                        min_value=reps_min,
                                        max_value=reps_max,
                                        value=default_reps,
                                        step=1,
                                        key=f"reps_{categoria}_{ejercicio}",
                                    )
                                else:
                                    default_reps = 10
                                    repeticiones = st.number_input(
                                        f"Repeticiones para {ejercicio}",
                                        min_value=1,
                                        max_value=500,
                                        value=default_reps,
                                        step=1,
                                        key=f"reps_{categoria}_{ejercicio}",
                                    )
                        ejercicios_seleccionados.append({
                            "categoria": categoria,
                            "nombre": ejercicio,
                            "musculos": obtener_musculos(ejercicio),
                            "repeticiones": repeticiones,
                        })

# Mostrar resumen
st.markdown('<p class="sub-header">Resumen del Entrenamiento</p>', unsafe_allow_html=True)

if ejercicios_seleccionados:
    ejercicios_para_descarga = ejercicios_seleccionados.copy()
    if tipo_circuito == "Tabata":
        ejercicios_requeridos = int(numero_ejercicios_tabata)
        if len(ejercicios_para_descarga) > ejercicios_requeridos:
            st.info(f"Se usarán los primeros {ejercicios_requeridos} ejercicios seleccionados para el protocolo Tabata.")
            ejercicios_para_descarga = ejercicios_para_descarga[:ejercicios_requeridos]
        if len(ejercicios_para_descarga) < ejercicios_requeridos:
            st.warning(f"Selecciona {ejercicios_requeridos} ejercicio(s) para completar tu Tabata.")
            tabata_listo = False
        else:
            plan_tabata = construir_tabata_plan(ejercicios_para_descarga)

    if es_circuito_entrenamiento:
        if len(ejercicios_para_descarga) < MIN_EJERCICIOS_CIRCUITO:
            st.warning(
                f"Selecciona al menos {MIN_EJERCICIOS_CIRCUITO} ejercicios para tu circuito de entrenamiento."
            )
            ejercicios_validos = False
        elif len(ejercicios_para_descarga) > MAX_EJERCICIOS_CIRCUITO:
            st.warning(
                f"Reduce la lista a un máximo de {MAX_EJERCICIOS_CIRCUITO} ejercicios para mantener la calidad del circuito."
            )
            ejercicios_validos = False

    if tabata_listo and ejercicios_validos:
        st.success(f"Se utilizarán {len(ejercicios_para_descarga)} ejercicio(s) en tu entrenamiento")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Ejercicios seleccionados:**")
        for idx, ejercicio in enumerate(ejercicios_para_descarga, 1):
            st.markdown(f"{idx}. **{ejercicio['nombre']}** ({ejercicio['categoria']})")
            reps_valor = ejercicio.get('repeticiones')
            reps_text = "-" if reps_valor in (None, "") else str(reps_valor)
            st.caption(f"Grupos musculares: {', '.join(ejercicio['musculos'])} | Reps: {reps_text}")
    
    with col2:
        st.markdown("**Configuración:**")
        st.markdown(f"- Tipo: {TIPOS_CIRCUITO[tipo_circuito]['nombre']}")
        if objetivo:
            st.markdown(f"- Objetivo: {objetivo}")
        if tipo_circuito in ["AMRAP", "EMOM"]:
            st.markdown(f"- Duración: {duracion} min")
            if tipo_circuito == "EMOM":
                st.markdown(f"- Recuperación: {EMOM_RECUPERACION_TEXTO}")
        elif tipo_circuito == "Tabata":
            st.markdown(f"- Ejercicios diferentes: {numero_ejercicios_tabata}")
            st.markdown("- Bloques: 8 (20\" trabajo / 10\" descanso)")
        else:
            st.markdown(f"- Rondas: {numero_rondas}")

        if objetivo and objetivo_info:
            st.markdown("**Parámetros del objetivo:**")
            st.caption(
                f"Carga: {objetivo_info['carga']} | Reps: {objetivo_info['reps']} | "
                f"Series: {objetivo_info['series']} | Descanso: {objetivo_info['descanso']} | "
                f"RIR: {objetivo_info['rir']}"
            )

        if tipo_circuito == "Ladder" and incremento is not None and reps_inicio is not None:
            st.markdown(f"- Repeticiones iniciales: {reps_inicio}")
            st.markdown(f"- Cambio por ronda: {incremento}")
            st.markdown(f"- Dirección: {ladder_direccion}")

        if plan_tabata:
            st.markdown("**Estructura Tabata:**")
            for bloque in plan_tabata:
                st.markdown(f"- {bloque['nombre']}: {bloque['bloques']} bloque(s) de 20\" trabajo + 10\" descanso")
else:
    st.warning("No has seleccionado ningún ejercicio. Por favor, selecciona al menos uno.")

# Clase de lienzo para añadir icono Creative Commons al final
class CreativeCommonsCanvas(canvas.Canvas):
    def __init__(self, *args, cc_image=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cc_image = cc_image
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_pages = len(self._saved_page_states)
        for idx, state in enumerate(self._saved_page_states, start=1):
            self.__dict__.update(state)
            if idx == total_pages:
                self._draw_cc_logo()
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def _draw_cc_logo(self):
        if not self.cc_image:
            return
        try:
            reader = ImageReader(io.BytesIO(self.cc_image))
        except Exception:
            return
        try:
            img_width, img_height = reader.getSize()
        except Exception:
            img_width = img_height = None
        max_width = 0.95 * inch
        max_height = 0.55 * inch
        if img_width and img_height and img_width > 0 and img_height > 0:
            scale = min(max_width / img_width, max_height / img_height)
            draw_width = img_width * scale
            draw_height = img_height * scale
        else:
            draw_width = draw_height = max_height
        x_pos = self._pagesize[0] - draw_width - 22
        y_pos = 18
        self.drawImage(reader, x_pos, y_pos, width=draw_width, height=draw_height, mask='auto')


# Función para generar PDF
def generar_pdf(nombre, grupo, tipo_circuito, ejercicios, parametros, plan_tabata=None, objetivo=None, objetivo_info=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=0.42*inch,
        bottomMargin=0.42*inch,
        leftMargin=0.45*inch,
        rightMargin=0.45*inch,
    )
    story = []
    styles = getSampleStyleSheet()
    font_regular, font_bold = obtener_fuentes_para_pdf()
    objetivo_info = objetivo_info or OBJETIVOS_ENTRENAMIENTO.get(objetivo)

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#FF6B6B'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName=font_bold
    )
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=15,
        textColor=colors.whitesmoke,
        fontName=font_bold
    )
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['BodyText'],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#1F2933'),
        fontName=font_regular
    )
    cell_bold = ParagraphStyle(
        'CellTextBold',
        parent=cell_style,
        fontName=font_bold
    )
    center_bold = ParagraphStyle(
        'CenterBold',
        parent=cell_bold,
        alignment=TA_CENTER,
        fontSize=11,
    )
    tipo_block_style = ParagraphStyle(
        'TipoBlock',
        parent=styles['BodyText'],
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#1F2933'),
        fontName=font_regular
    )

    def construir_icono(icono_tipo: Optional[str], ancho: float) -> Optional[RLImage]:
        if not icono_tipo:
            return None
        icono_bytes = generar_icono_decorativo(icono_tipo)
        if not icono_bytes:
            return None
        return RLImage(io.BytesIO(icono_bytes), width=ancho, height=ancho)

    def wrap_flow(flowable, width, height):
        return KeepInFrame(width, height, [flowable], mode='shrink')

    def construir_encabezado(titulo: str, icono_tipo: Optional[str], color_fondo: str):
        icon_flow = construir_icono(icono_tipo, 0.42*inch) if icono_tipo else None
        if icon_flow:
            data = [[icon_flow, Paragraph(titulo.upper(), section_header_style)]]
            col_widths = [0.5*inch, doc.width - 0.5*inch]
        else:
            data = [[Paragraph(titulo.upper(), section_header_style)]]
            col_widths = [doc.width]
        header = Table(data, colWidths=col_widths)
        header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(color_fondo)),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return header

    def agregar_bloque(titulo: str, contenido, icono_tipo: Optional[str] = None, color_fondo: str = '#2F3C7E'):
        contenido_list = contenido if isinstance(contenido, list) else [contenido]
        elementos = [construir_encabezado(titulo, icono_tipo, color_fondo), Spacer(1, 0.08*inch)]
        elementos.extend(contenido_list)
        story.append(KeepTogether(elementos))
        story.append(Spacer(1, 0.12*inch))

    def construir_lista_puntos(textos):
        data = [[Paragraph("•", cell_bold), Paragraph(texto, cell_style)] for texto in textos]
        tabla = Table(data, colWidths=[0.18*inch, doc.width - 0.18*inch])
        tabla.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1F2933')),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        return tabla

    def construir_tabla_borg():
        data = [[Paragraph("Sensación", cell_bold), Paragraph("Descripción", cell_bold)]]
        for nivel in BORG_ESCALA:
            data.append([
                Paragraph(nivel['nivel'], cell_style),
                Paragraph(nivel['descripcion'], cell_style)
            ])
        tabla = Table(data, colWidths=[0.34*doc.width, 0.66*doc.width])
        estilo = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E7FF')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1E1B4B')),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#E5E7EB')),
        ]
        for idx, nivel in enumerate(BORG_ESCALA, start=1):
            estilo.append(('BACKGROUND', (0, idx), (-1, idx), colors.HexColor(nivel['color'])))
        tabla.setStyle(TableStyle(estilo))
        return tabla

    encabezado_img = None
    if ENCABEZADO_IMG.exists():
        encabezado_img = RLImage(str(ENCABEZADO_IMG), width=doc.width, height=doc.width * 0.28)
    if encabezado_img:
        encabezado_img.hAlign = 'CENTER'
        story.append(KeepTogether([encabezado_img]))
        story.append(Spacer(1, 0.05*inch))
    else:
        story.append(Paragraph("Entrenamiento CrossFit", title_style))
        story.append(Spacer(1, 0.05*inch))

    icono_pdf_bytes = obtener_icono_profesor_pdf_bytes()
    icon_img = None
    if icono_pdf_bytes:
        icon_img = RLImage(io.BytesIO(icono_pdf_bytes), width=0.9*inch, height=0.9*inch)
    elif ICONO_PROFESOR.exists():
        icon_img = RLImage(str(ICONO_PROFESOR), width=0.85*inch, height=0.85*inch)

    autor_text = Paragraph(
        f"{PROFESOR_NOMBRE}<br/><font size=9 color='#475569'>{PROFESOR_EMAIL}</font>",
        cell_bold,
    )

    if icon_img:
        icon_img.hAlign = 'LEFT'
        autor = Table(
            [[icon_img, autor_text]],
            colWidths=[1.0*inch, doc.width - 1.0*inch]
        )
        autor.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(autor)
    else:
        story.append(autor_text)

    story.append(Spacer(1, 0.12*inch))

    info_row = [
        Paragraph(f"<b>Nombre:</b> {nombre}", cell_style),
        Paragraph(f"<b>Grupo:</b> {grupo}", cell_style),
        Paragraph(f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y')}", cell_style),
    ]
    info_table = Table([info_row], colWidths=[0.38*doc.width, 0.26*doc.width, 0.36*doc.width])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F7F9FC')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1F2933')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), font_regular),
        ('FONTSIZE', (0, 0), (-1, -1), 10.5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#E0E4EC')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E4EC')),
    ]))
    story.append(KeepTogether([info_table]))
    story.append(Spacer(1, 0.1*inch))

    target_icon_flow = construir_icono('target', 1.0*inch)
    if target_icon_flow:
        tipo_icon = wrap_flow(target_icon_flow, 1.05*inch, 1.05*inch)
    else:
        tipo_icon = Spacer(1.0*inch, 1.0*inch)
    texto_tipo = (
        "<font size=9 color='#B5179E'>WOD</font><br/>"
        f"<font size=18 color='#B5179E'><b>{TIPOS_CIRCUITO[tipo_circuito]['nombre']}</b></font><br/>"
        f"<font size=11 color='#1F2933'>{TIPOS_CIRCUITO[tipo_circuito]['descripcion']}</font>"
    )
    tipo_text = wrap_flow(Paragraph(texto_tipo, tipo_block_style), max(doc.width * 0.56, 2.8*inch), 1.35*inch)
    texto_width = doc.width - 1.05*inch
    tipo_card = Table(
        [[tipo_icon, tipo_text]],
        colWidths=[1.05*inch, texto_width]
    )
    tipo_card.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF4EE')),
        ('BOX', (0, 0), (-1, -1), 0.9, colors.HexColor('#F5C9B5')),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#FBE1D2')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(KeepTogether([tipo_card]))
    story.append(Spacer(1, 0.16*inch))

    notas = [
        "Realiza un calentamiento de 5-10 minutos antes de comenzar",
        "Mantén una técnica correcta en todo momento",
        "Hidrátate adecuadamente durante el entrenamiento",
        "Escucha a tu cuerpo y ajusta la intensidad si es necesario",
        "Realiza estiramientos al finalizar (5-10 minutos)",
    ]
    notas_table = construir_lista_puntos(notas)
    agregar_bloque("Notas importantes", [notas_table], icono_tipo="notes", color_fondo='#92400E')

    if parametros:
        param_rows = [[Paragraph(key, cell_bold), Paragraph(str(value), cell_style)] for key, value in parametros.items()]
        param_table = Table(param_rows, colWidths=[0.38*doc.width, 0.62*doc.width])
        param_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#111111')),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#D9DEE7')),
        ]))
        agregar_bloque("Parámetros configurados", [param_table], icono_tipo="settings", color_fondo='#1F4172')

    if objetivo and objetivo_info:
        objetivo_rows = []
        for etiqueta, campo in [
            ("Objetivo", objetivo),
            ("Carga", objetivo_info['carga']),
            ("Repeticiones", objetivo_info['reps']),
            ("Series", objetivo_info['series']),
            ("Descanso", objetivo_info['descanso']),
            ("RIR", objetivo_info['rir']),
        ]:
            objetivo_rows.append([Paragraph(etiqueta, cell_bold), Paragraph(campo, cell_style)])
        objetivo_table = Table(objetivo_rows, colWidths=[0.34*doc.width, 0.66*doc.width])
        objetivo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF7ED')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#FFF1DB')]),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#F4C7A1')),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        agregar_bloque("Objetivo del entrenamiento", [objetivo_table], icono_tipo="summit", color_fondo='#B42318')

    if objetivo:
        tabla_resumen = [["Objetivo", "%1RM", "Reps", "Series", "Descanso", "RIR"]]
        for nombre in OBJETIVOS_ORDEN:
            datos = OBJETIVOS_ENTRENAMIENTO[nombre]
            tabla_resumen.append([
                Paragraph(nombre, cell_style),
                Paragraph(datos['porcentaje'], cell_style),
                Paragraph(datos['reps'], cell_style),
                Paragraph(datos['series'], cell_style),
                Paragraph(datos['descanso'], cell_style),
                Paragraph(datos['rir'], cell_style),
            ])
        resumen_table = Table(
            tabla_resumen,
            colWidths=[0.22*doc.width, 0.14*doc.width, 0.14*doc.width, 0.14*doc.width, 0.2*doc.width, 0.16*doc.width]
        )
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#CBD5F5')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#EEF2FF')])
        ]))
        agregar_bloque("Tabla guía de objetivos", [resumen_table], icono_tipo="settings", color_fondo='#0F172A')

    if plan_tabata:
        plan_data = [["Ejercicio", 'Bloques (20" trabajo / 10" descanso)']]
        for item in plan_tabata:
            plan_data.append([
                Paragraph(item['nombre'], cell_style),
                Paragraph(str(item['bloques']), cell_style)
            ])
        plan_table = Table(plan_data, colWidths=[0.68*doc.width, 0.32*doc.width])
        plan_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B6B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (-1, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#F9DCDC')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF2F2')])
        ]))
        tabata_url = "https://youtu.be/V67eNoSYwNE"
        enlace_parrafo = (
            f"<font size=10>Escanea el código QR o usa este enlace: "
            f"<link href='{tabata_url}' color='blue'>{tabata_url}</link></font>"
        )
        plan_content = [plan_table, Spacer(1, 0.08*inch), Paragraph(enlace_parrafo, cell_style), Spacer(1, 0.06*inch)]
        try:
            qr_widget = qr.QrCodeWidget(tabata_url)
            bounds = qr_widget.getBounds()
            width_qr = bounds[2] - bounds[0]
            height_qr = bounds[3] - bounds[1]
            size_qr = 1.6 * inch
            drawing = Drawing(size_qr, size_qr, transform=[size_qr / width_qr, 0, 0, size_qr / height_qr, 0, 0])
            drawing.add(qr_widget)
            plan_content.append(drawing)
        except Exception:
            pass
        agregar_bloque("Plan Tabata", plan_content, icono_tipo="timer", color_fondo='#A02334')

    ejercicios_data = [["#", "Ejercicio", "Categoría", "Grupos musculares", "Reps"]]
    for idx, ej in enumerate(ejercicios, 1):
        grupos = ", ".join(ej.get('musculos', obtener_musculos(ej['nombre'])))
        reps_text = "-" if ej.get('repeticiones') in (None, "") else str(ej.get('repeticiones'))
        ejercicios_data.append([
            str(idx),
            Paragraph(ej['nombre'], cell_style),
            Paragraph(ej['categoria'], cell_style),
            Paragraph(grupos, cell_style),
            Paragraph(reps_text, cell_style),
        ])
    tabla_ancho = doc.width
    ejercicios_table = Table(
        ejercicios_data,
        colWidths=[
            0.07 * tabla_ancho,
            0.32 * tabla_ancho,
            0.18 * tabla_ancho,
            0.31 * tabla_ancho,
            0.12 * tabla_ancho,
        ]
    )
    ejercicios_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4ECDC4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (-1, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#B7E4DC')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2FFFC')])
    ]))
    agregar_bloque("Ejercicios del WOD", [ejercicios_table], icono_tipo="dumbbell", color_fondo='#0F766E')

    borg_table = construir_tabla_borg()
    agregar_bloque(
        "Percepción subjetiva del esfuerzo (Escala de Borg)",
        [borg_table],
        icono_tipo="notes",
        color_fondo='#7C3AED'
    )

    beneficios_especificos = BENEFICIOS_WOD.get(
        tipo_circuito,
        BENEFICIOS_WOD.get(CIRCUITO_ENTRENAMIENTO_KEY, []),
    )
    if beneficios_especificos:
        tabla_beneficios = construir_lista_puntos(beneficios_especificos)
        agregar_bloque(
            "Beneficios específicos del WOD",
            [tabla_beneficios],
            icono_tipo="performance",
            color_fondo='#2563EB'
        )

    tabla_beneficios_generales = construir_lista_puntos(BENEFICIOS_OTROS)
    agregar_bloque(
        "Otros beneficios",
        [tabla_beneficios_generales],
        icono_tipo="wellbeing",
        color_fondo='#4C1D95'
    )

    registro_table = Table(
        [
            [Paragraph("<b>Tiempo invertido / Rondas o repeticiones completadas</b>", cell_bold)],
            [Paragraph("\n\n", cell_style)],
            [Paragraph("<b>Observaciones</b>", cell_bold)],
            [Paragraph("\n\n\n", cell_style)],
        ],
        colWidths=[doc.width],
        rowHeights=[None, 0.4*inch, None, 1.1*inch]
    )
    registro_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5F5')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    agregar_bloque("Registro del entrenamiento", [registro_table], icono_tipo="settings", color_fondo='#0F172A')
    story.append(Paragraph("¡Disfruta de tu entrenamiento!", center_bold))
    story.append(Spacer(1, 0.12*inch))

    cc_icon_bytes = obtener_logo_creative_commons()
    doc.build(
        story,
        canvasmaker=lambda *args, **kwargs: CreativeCommonsCanvas(*args, cc_image=cc_icon_bytes, **kwargs)
    )
    buffer.seek(0)
    return buffer

# Botón de descarga
if ejercicios_para_descarga and nombre and grupo and tabata_listo and ejercicios_validos:
    st.markdown("---")
    
    # Preparar parámetros para el PDF
    parametros = {}
    if objetivo:
        parametros["Objetivo"] = objetivo
    if tipo_circuito in ["AMRAP", "EMOM"]:
        parametros["Duración"] = f"{duracion} minutos"
        if tipo_circuito == "EMOM":
            parametros["Recuperación"] = EMOM_RECUPERACION_TEXTO
    elif tipo_circuito == "Tabata":
        parametros["Número de ejercicios"] = numero_ejercicios_tabata
        parametros["Bloques Tabata"] = "8 bloques (20\" trabajo + 10\" descanso)"
    else:
        parametros["Número de rondas"] = numero_rondas
    
    if tipo_circuito == "Ladder":
        parametros["Incremento"] = incremento
        parametros["Repeticiones iniciales"] = reps_inicio
        parametros["Dirección"] = ladder_direccion
        if all(value is not None for value in (numero_rondas, reps_inicio, incremento)):
            try:
                rep_actual = int(reps_inicio)
                salto = int(incremento)
                rondas = int(numero_rondas)
            except (TypeError, ValueError):
                rep_actual = salto = rondas = None
            if rep_actual is not None and salto is not None and rondas is not None and rondas > 0:
                desglose = []
                for _ in range(rondas):
                    desglose.append(max(1, rep_actual))
                    if ladder_direccion == "Creciente":
                        rep_actual += salto
                    else:
                        rep_actual = max(1, rep_actual - salto)
                parametros["Desglose"] = "-".join(str(val) for val in desglose)
    elif tipo_circuito != "Tabata":
        parametros["Repeticiones"] = "Personalizadas por ejercicio"
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pdf_buffer = generar_pdf(
            nombre,
            grupo,
            tipo_circuito,
            ejercicios_para_descarga,
            parametros,
            plan_tabata,
            objetivo,
            objetivo_info,
        )
        
        st.download_button(
            label="Descargar Entrenamiento (PDF)",
            data=pdf_buffer,
            file_name=f"Entrenamiento_CrossFit_{nombre.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            on_click=lambda: st.session_state.__setitem__("registrar_descarga", True),
        )
        
        st.success("¡Todo listo! Haz clic en el botón para descargar tu entrenamiento personalizado.")
elif not nombre or not grupo:
    st.warning("Por favor, completa tu nombre y grupo en la barra lateral.")
    
# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #888;'>
        <p>Generador de Entrenamientos CrossFit v1.0<br/>
        Diseñado para estudiantes de secundaria</p>
    </div>
""", unsafe_allow_html=True)
