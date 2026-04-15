# Shikaku Puzzle Solver 🟦🔢

Este proyecto es un solucionador y juego interactivo del rompecabezas japonés **Shikaku** (también conocido como *Rectangles*). Desarrollado como parte del curso de Análisis de Algoritmos en la Pontificia Universidad Javeriana (2026).

El proyecto incluye un motor de resolución basado en **Backtracking optimizado** y una interfaz gráfica moderna construida con **Pygame**.

## 🚀 Características

- **Interfaz Gráfica Premium**: Tema oscuro moderno con efectos visuales y animaciones.
- **Modo Humano**: Juega e intenta resolver los puzzles manualmente.
- **Modo Sintético (Solver)**: Observa cómo el algoritmo de backtracking encuentra la solución en milisegundos.
- **Múltiples Niveles**: Desde tutoriales de 4x4 hasta desafíos expertos de 10x10.
- **CLI Mode**: Solucionador por consola para pruebas de rendimiento.

## 📋 Reglas del Juego

1. El tablero debe dividirse completamente en rectángulos.
2. Cada rectángulo debe contener **exactamente un número**.
3. El número indica el **área** del rectángulo (número de celdas).
4. Los rectángulos no pueden solaparse.

## 🛠️ Instalación

Asegúrate de tener Python 3.10 o superior instalado. Para instalar las dependencias necesarias, ejecuta:

```bash
pip install pygame-ce
```

> [!NOTE]
> Se recomienda el uso de **pygame-ce** para asegurar la compatibilidad con las últimas versiones de Python y las mejoras de rendimiento en la interfaz.

## 🎮 Uso

### Iniciar el Juego (GUI)
Para lanzar la interfaz gráfica y jugar o ver el solucionador en acción:

```bash
python main.py
```

### Modo Consola (CLI)
Si deseas ejecutar solo el algoritmo de resolución en el terminal:

```bash
# Resolver todos los puzzles precargados
python main.py --cli

# Resolver un puzzle específico por su índice (ej: el nivel 3)
python main.py --cli 3
```

## 🧠 Algoritmo de Resolución

El motor de solución utiliza un algoritmo de **vuelta atrás (Backtracking)** con las siguientes optimizaciones de poda:

- **Fail-First Strategy**: El algoritmo comienza procesando las pistas que tienen menos candidatos posibles para reducir drásticamente el árbol de búsqueda.
- **Propagación de Restricciones**: Verifica colisiones y solapamientos en tiempo real antes de profundizar en la búsqueda.

## ✒️ Autores

- **Sebastian** - *Desarrollo Inicial y Algoritmos*
- Proyecto para: **Análisis de Algoritmos - Javeriana 2026-10**

---
⭐ Si te resulta útil este solucionador, no olvides darle una estrella al repositorio.
