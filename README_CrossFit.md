# 💪 Generador de Entrenamientos CrossFit

Aplicación web diseñada para estudiantes de secundaria que desean crear sus propios entrenamientos de CrossFit personalizados.

## 🎯 Características

- **Información personal**: Los estudiantes pueden ingresar su nombre y grupo
- **Múltiples categorías de ejercicios**:
  - Autocarga (flexiones, burpees, sentadillas, etc.)
  - Barra Olímpica (deadlift, squat, clean, etc.)
  - Mancuernas
  - Kettlebell
  - TRX
  - Cajón (box jumps)
  - Medicine Ball

- **6 Tipos de circuitos**:
  - **AMRAP** (As Many Rounds As Possible)
  - **EMOM** (Every Minute On the Minute)
  - **Tabata**
  - **For Time**
  - **Ladder** (Escalera)
  - **AFAP** (As Fast As Possible)

- **Personalización completa**: Ajusta duración, repeticiones, descansos, etc.
- **Descarga en PDF**: Genera un documento profesional con todo el entrenamiento

## 📋 Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## 🚀 Instalación

1. **Instala las dependencias**:
```bash
pip install -r requirements_crossfit.txt
```

2. **Ejecuta la aplicación**:
```bash
streamlit run crossfit_trainer.py
```

3. **Abre tu navegador**:
La aplicación se abrirá automáticamente en `http://localhost:8501`

## 📖 Cómo usar

1. **Completa tu información** en la barra lateral:
   - Nombre completo
   - Grupo (ej: 3°A)

2. **Selecciona el tipo de circuito** que quieres realizar

3. **Elige tus ejercicios**:
   - Navega por las pestañas de cada categoría
   - Marca los ejercicios que quieres incluir

4. **Ajusta los parámetros**:
   - Duración o número de rondas
   - Repeticiones por ejercicio
   - Tiempo de descanso

5. **Descarga tu entrenamiento**:
   - Haz clic en "Descargar Entrenamiento (PDF)"
   - Se generará un documento con toda la información

## 📄 El PDF incluye

- Información del alumno (nombre, grupo, fecha)
- Tipo de circuito y descripción
- Parámetros configurados
- Lista completa de ejercicios con categorías
- Notas importantes y recomendaciones de seguridad

## 🎨 Interfaz

La aplicación tiene un diseño moderno y colorido, fácil de usar para estudiantes:
- Colores llamativos y emojis
- Organización clara por secciones
- Instrucciones paso a paso
- Resumen visual del entrenamiento

## ⚡ Tipos de Circuito Explicados

### AMRAP (As Many Rounds As Possible)
Completa tantas rondas como puedas en el tiempo establecido (ej: 15 minutos)

### EMOM (Every Minute On the Minute)
Cada minuto comienza una nueva serie de ejercicios. Descansas el tiempo sobrante.

### Tabata
20 segundos de trabajo intenso + 10 segundos de descanso, repetir 8 veces por ejercicio

### For Time
Completa el circuito lo más rápido posible dentro del tiempo límite

### Ladder (Escalera)
Las repeticiones aumentan o disminuyen en cada ronda (ej: 5, 7, 9, 11...)

### AFAP (As Fast As Possible)
Completa las repeticiones establecidas lo más rápido que puedas

## 🔧 Personalización

Puedes modificar el archivo `crossfit_trainer.py` para:
- Añadir más ejercicios
- Agregar nuevas categorías
- Crear nuevos tipos de circuitos
- Cambiar los colores y estilos

## 📚 Recursos Adicionales

- [Documentación de Streamlit](https://docs.streamlit.io/)
- [Guía de CrossFit para principiantes](https://www.crossfit.com/get-started)

## ⚠️ Advertencias de Seguridad

- Siempre realiza un calentamiento antes de empezar
- Mantén una técnica correcta para evitar lesiones
- Consulta con un profesor o entrenador si tienes dudas
- Escucha a tu cuerpo y ajusta la intensidad según sea necesario

## 🤝 Soporte

Si encuentras algún problema o tienes sugerencias, por favor contacta con tu profesor de educación física.

---

**¡Disfruta creando tus entrenamientos personalizados! 💪🏋️‍♂️**
