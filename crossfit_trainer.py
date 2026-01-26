import base64
import io
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
)

# Configuración de la página
st.set_page_config(
    page_title="Generador de Entrenamientos CrossFit",
    page_icon="CF",
    layout="wide"
)

BASE_DIR = Path(__file__).parent
ICONO_PROFESOR = BASE_DIR / "iconoentrena.jpg"
EMOJI_FONT_PATH = Path("C:/Windows/Fonts/seguiemj.ttf")
EMOJI_FONT_REGULAR_NAME = "SegoeUIEmoji"
EMOJI_FONT_BOLD_NAME = "SegoeUIEmoji-Bold"
DEFAULT_FONT_REGULAR = "Helvetica"
DEFAULT_FONT_BOLD = "Helvetica-Bold"


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

    draw_funcs = {
        "target": draw_target,
        "strength": draw_strength,
        "notes": draw_notes,
        "settings": draw_settings,
        "timer": draw_timer,
    }

    painter = draw_funcs.get(tipo)
    if painter is None:
        return None

    painter()
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

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
            <span style='font-size:1.2rem; font-weight:600; color:#2C3E50;'>Profesor Víctor Manuel Marcos Muñoz</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown("### Profesor Víctor Manuel Marcos Muñoz")

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
}
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
    }
}

EJERCICIOS_INFO = {
    "Flexiones (Push-ups)": ["Pectoral", "Tríceps", "Core"],
    "Sentadillas (Air Squats)": ["Cuádriceps", "Glúteos", "Core"],
    "Burpees": ["Cuerpo completo", "Cardio"],
    "Jumping Jacks": ["Hombros", "Piernas", "Cardio"],
    "Mountain Climbers": ["Core", "Hombros", "Cardio"],
    "Plank Hold": ["Core", "Hombros", "Lumbar"],
    "Lunges (Zancadas)": ["Cuádriceps", "Glúteos", "Isquiotibiales"],
    "Jump Squats": ["Cuádriceps", "Glúteos", "Pantorrillas"],
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
    nombre = st.text_input("Nombre completo:", placeholder="Ej: Juan Pérez")
    grupo = st.text_input("Grupo:", placeholder="Ej: 3°A")
    
    st.markdown("---")
    st.markdown("### 📖 Instrucciones")
    st.markdown("""
    1. Completa tu información
    2. Selecciona el tipo de circuito
    3. Elige tus ejercicios favoritos
    4. Ajusta parámetros
    5. ¡Descarga tu entrenamiento!
    """)

# Sección principal - Selección de tipo de circuito
st.markdown('<p class="sub-header">Tipo de Circuito</p>', unsafe_allow_html=True)
tipo_circuito = st.selectbox(
    "Selecciona el tipo de circuito:",
    options=list(TIPOS_CIRCUITO.keys()),
    format_func=lambda x: TIPOS_CIRCUITO[x]["nombre"]
)

# Mostrar información del circuito seleccionado
col1, col2 = st.columns(2)
with col1:
    st.info(f"**Descripción:** {TIPOS_CIRCUITO[tipo_circuito]['descripcion']}")
with col2:
    st.info(f"**Duración sugerida:** {TIPOS_CIRCUITO[tipo_circuito]['duracion_sugerida']}")

# Parámetros del circuito
st.markdown('<p class="sub-header">Parámetros del Circuito</p>', unsafe_allow_html=True)

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

# Crear tabs para cada categoría
tabs = st.tabs(list(EJERCICIOS.keys()))

for idx, (categoria, ejercicios) in enumerate(EJERCICIOS.items()):
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

    if tabata_listo:
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
        if tipo_circuito in ["AMRAP", "EMOM"]:
            st.markdown(f"- Duración: {duracion} min")
        elif tipo_circuito == "Tabata":
            st.markdown(f"- Ejercicios diferentes: {numero_ejercicios_tabata}")
            st.markdown("- Bloques: 8 (20\" trabajo / 10\" descanso)")
        else:
            st.markdown(f"- Rondas: {numero_rondas}")

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

# Función para generar PDF
def generar_pdf(nombre, grupo, tipo_circuito, ejercicios, parametros, plan_tabata=None):
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

    def agregar_seccion(titulo: str, icono_tipo: Optional[str] = None, color_fondo: str = '#2F3C7E'):
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
        story.append(header)
        story.append(Spacer(1, 0.08*inch))

    story.append(Paragraph("💪Entrenamiento CrossFit💪", title_style))
    story.append(Spacer(1, 0.05*inch))

    icono_pdf_bytes = obtener_icono_profesor_pdf_bytes()
    icon_img = None
    if icono_pdf_bytes:
        icon_img = RLImage(io.BytesIO(icono_pdf_bytes), width=0.9*inch, height=0.9*inch)
    elif ICONO_PROFESOR.exists():
        icon_img = RLImage(str(ICONO_PROFESOR), width=0.85*inch, height=0.85*inch)

    if icon_img:
        icon_img.hAlign = 'LEFT'
        autor = Table(
            [[icon_img, Paragraph("Profesor Víctor Manuel Marcos Muñoz", cell_bold)]],
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
        story.append(Paragraph("Profesor Víctor Manuel Marcos Muñoz", cell_bold))

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
    story.append(info_table)
    story.append(Spacer(1, 0.1*inch))

    target_icon_flow = construir_icono('target', 1.0*inch)
    if target_icon_flow:
        tipo_icon = wrap_flow(target_icon_flow, 1.05*inch, 1.05*inch)
    else:
        tipo_icon = Spacer(1.0*inch, 1.0*inch)
    texto_tipo = (
        "<font size=9 color='#B5179E'>TIPO DE CIRCUITO</font><br/>"
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
    story.append(tipo_card)
    story.append(Spacer(1, 0.16*inch))

    if parametros:
        agregar_seccion("Parámetros configurados", icono_tipo="settings", color_fondo='#1F4172')
        param_rows = []
        for key, value in parametros.items():
            param_rows.append([
                Paragraph(key, cell_bold),
                Paragraph(str(value), cell_style)
            ])
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
        story.append(param_table)
        story.append(Spacer(1, 0.12*inch))

    if plan_tabata:
        agregar_seccion("Plan Tabata", icono_tipo="timer", color_fondo='#A02334')
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
        story.append(plan_table)
        story.append(Spacer(1, 0.12*inch))

    agregar_seccion("Ejercicios del circuito", icono_tipo="strength", color_fondo='#0F766E')
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
    story.append(ejercicios_table)
    story.append(Spacer(1, 0.16*inch))

    agregar_seccion("Notas importantes", icono_tipo="notes", color_fondo='#92400E')
    notas = [
        "Realiza un calentamiento de 5-10 minutos antes de comenzar",
        "Mantén una técnica correcta en todo momento",
        "Hidrátate adecuadamente durante el entrenamiento",
        "Escucha a tu cuerpo y ajusta la intensidad si es necesario",
        "Realiza estiramientos al finalizar (5-10 minutos)",
    ]
    notas_data = [[Paragraph("•", cell_bold), Paragraph(texto, cell_style)] for texto in notas]
    notas_table = Table(notas_data, colWidths=[0.18*inch, doc.width - 0.18*inch])
    notas_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1F2933')),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(notas_table)

    doc.build(story)
    buffer.seek(0)
    return buffer

# Botón de descarga
if ejercicios_para_descarga and nombre and grupo and tabata_listo:
    st.markdown("---")
    
    # Preparar parámetros para el PDF
    parametros = {}
    if tipo_circuito in ["AMRAP", "EMOM"]:
        parametros["Duración"] = f"{duracion} minutos"
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
        pdf_buffer = generar_pdf(nombre, grupo, tipo_circuito, ejercicios_para_descarga, parametros, plan_tabata)
        
        st.download_button(
            label="Descargar Entrenamiento (PDF)",
            data=pdf_buffer,
            file_name=f"Entrenamiento_CrossFit_{nombre.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
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
