# Diseño de páginas (desktop-first) — Reloj analógico

## Global Styles (tokens)
- Canvas/base background: `#0B1020` (dark) / `#F7F8FA` (light)
- Surface/cards: `#121A33` (dark) / `#FFFFFF` (light)
- Accent: `#4F46E5` (primary), `#22C55E` (success), `#EF4444` (danger)
- Typography: Inter/System UI; scale 14/16/20/24/32
- Buttons:
  - Primary: accent background + white text; hover: +8% brightness; active: slight scale(0.98)
  - Secondary: transparent + border; hover: subtle surface tint
- Links: accent color, underline on hover
- Focus states: 2px outline accent, accessible contrast

## Layout & Responsive behavior
- Enfoque desktop-first, grid de 12 columnas, max-width 1200–1280px centrado.
- Breakpoints sugeridos:
  - Desktop: ≥ 1024px (layout principal)
  - Tablet: 768–1023px (columna única, reloj arriba)
  - Mobile: ≤ 767px (espaciado reducido, controles apilados)
- Sistema: CSS Grid para estructura general + Flexbox dentro de componentes.

---

## Página: Reloj (Inicio)

### Meta Information
- Title: "Analog Clock"
- Description: "Analog clock demo powered by a doubly circular linked list."
- Open Graph:
  - og:title: "Analog Clock"
  - og:description: "Analog clock demo powered by a doubly circular linked list."

### Page Structure
- Header fijo (alto 56–64px): logo/nombre + navegación.
- Main en 2 columnas (desktop):
  - Columna izquierda (≈ 65%): reloj (card principal).
  - Columna derecha (≈ 35%): panel de controles + estado.
- Footer ligero con enlace a About.

### Sections & Components
1) **Top Navigation (Header)**
   - Contiene: nombre del proyecto + tabs/links: Clock, Settings, About.
   - Estado activo destacado (underline o pill).

2) **Clock Card**
   - Render: SVG (recomendado por nitidez) o Canvas.
   - Elementos:
     - Dial circle + inner shadow.
     - 60 tick marks (12 más gruesas).
     - Números 12/3/6/9 (mínimo) o los 12.
     - Manecillas: hour/minute/second.
     - Punto central (cap).
   - Interacción:
     - No editable; solo re-render al recibir nuevo `ClockState`.

3) **Controls Panel**
   - Botones:
     - Start/Pause (toggle)
     - Mode: Realtime / Simulated (segmented control)
     - Reset (solo visible en simulated)
   - Inputs (si mode=simulated): speed selector (x1/x2/x10) y set time.

4) **Status Bar**
   - Texto: hora digital, mode, running.
   - Muestra el `isoTime` formateado (HH:MM:SS) y un badge.

### Interaction states
- Loading: skeleton o spinner pequeño en panel (si API tarda).
- Error: banner rojo con “Retry”.
- Transiciones: 150–200ms en hover/active de controles.

---

## Página: Configuración

### Meta Information
- Title: "Settings"
- Description: "Customize appearance and motion of the clock."

### Page Structure
- Layout de formulario en card central (max 720px) + preview lateral en desktop.
- Desktop: 2 columnas (form + preview mini).
- Tablet/mobile: una columna con preview arriba.

### Sections & Components
1) **Settings Form (Card)**
   - Grupo Appearance:
     - Theme selector (light/dark)
     - Size slider/input (px)
     - Hand thickness/color (mínimo: thickness)
   - Grupo Motion:
     - Smooth motion toggle
     - Refresh rate selector (e.g., 10/30/60)
   - Grupo Time Source:
     - Time zone selector (local + texto)
     - Simulation speed (si aplica)

2) **Actions**
   - Save (primary)
   - Reset to defaults (secondary)

3) **Preview**
   - Mini reloj con el mismo render component reutilizado.

### Validation
- Size: rango mínimo/máximo (p.ej. 200–800).
- RefreshHz: valores permitidos.

---

## Página: Acerca de / Guía

### Meta Information
- Title: "About"
- Description: "How the doubly circular linked list powers the clock."

### Page Structure
- Página de lectura tipo documentación.
- Contenido en secciones con anclas (toc lateral opcional en desktop).

### Sections & Components
1) **Intro**
   - Qué es el proyecto y objetivo didáctico.

2) **Core Idea: Doubly Circular Linked List**
   - Explicar que existen 60 nodos (0..59) conectados next/prev.
   - Cómo moverse forward/backward para representar ticks.

3) **How it maps to the dial**
   - Regla de mapeo: `index -> degrees` y cómo se obtienen marcas/ángulos.

4) **Run Instructions (alto nivel)**
   - Backend: instalar deps y correr servidor.
   - Frontend: instalar deps y levantar dev server.

5) **Prompts por partes**
   - Repetir/mostrar prompts (copiables) para generar el código en inglés.

---

## Component inventory (reutilizable)
- `AnalogClock` (SVG/Canvas renderer)
- `ClockControls`
- `SettingsForm`
- `TopNav`
- `StatusBadge`
- `ErrorBanner`
