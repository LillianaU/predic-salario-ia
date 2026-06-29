---
name: PredicSalario IA
colors:
  surface: '#f9f9ff'
  surface-dim: '#cfdaf2'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3ff'
  surface-container: '#e7eeff'
  surface-container-high: '#dee8ff'
  surface-container-highest: '#d8e3fb'
  on-surface: '#111c2d'
  on-surface-variant: '#3c4a46'
  inverse-surface: '#263143'
  inverse-on-surface: '#ecf1ff'
  outline: '#6b7a76'
  outline-variant: '#bacac5'
  surface-tint: '#006b5f'
  primary: '#006b5f'
  on-primary: '#ffffff'
  primary-container: '#2dd4bf'
  on-primary-container: '#00574d'
  inverse-primary: '#3cddc7'
  secondary: '#006a63'
  on-secondary: '#ffffff'
  secondary-container: '#99efe5'
  on-secondary-container: '#006f67'
  tertiary: '#55615f'
  on-tertiary: '#ffffff'
  tertiary-container: '#b4c1be'
  on-tertiary-container: '#434f4d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#62fae3'
  primary-fixed-dim: '#3cddc7'
  on-primary-fixed: '#00201c'
  on-primary-fixed-variant: '#005047'
  secondary-fixed: '#9cf2e8'
  secondary-fixed-dim: '#80d5cb'
  on-secondary-fixed: '#00201d'
  on-secondary-fixed-variant: '#00504a'
  tertiary-fixed: '#d8e5e2'
  tertiary-fixed-dim: '#bcc9c6'
  on-tertiary-fixed: '#121e1c'
  on-tertiary-fixed-variant: '#3d4947'
  background: '#f9f9ff'
  on-background: '#111c2d'
  surface-variant: '#d8e3fb'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Hanken Grotesk
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-mono:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
  headline-md-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  container-max: 1440px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 32px
  sidebar-width: 260px
---

## Brand & Style
El sistema de diseno de PredicSalario IA se basa en **Corporate Modernism** con enfoque en visualizacion de datos de alta densidad y claridad profesional. La audiencia objetivo son analistas de datos y profesionales TI que requieren una herramienta precisa, performante y confiable.

La estetica utiliza un enfoque "Clean Tech": espacio blanco significativo, tipografia de alta precision y uso refinado de la paleta teal primaria para atraer la atencion a elementos interactivos e insights. El area de trabajo principal es clara y aireada para reducir carga cognitiva durante sesiones largas.

## Colors
La paleta esta dominada por un fondo blanco clinico (`#ffffff`) para maximizar la legibilidad de graficos y tablas complejas.

El **Teal Primario (#2dd4bf)** es el color interactivo signature, usado para acciones principales, estados de exito y highlights de datos. Para mantener presencia de marca en modo claro, la barra lateral utiliza un enfoque dark-mode-inverso con fondo navy-teal profundo (`#0f172a`).

Para el modo oscuro, mantener el mismo teal primario pero invertir la escala neutral, transicionando el surface-main a charcoal profundo y el text-primary a off-white.

## Typography
El sistema tipografico equilibra caracter con utilidad. **Hanken Grotesk** proporciona un feel contemporaneo para titulos. **Inter** se utiliza para todo el texto de cuerpo y elementos de interfaz. **JetBrains Mono** se reserva para etiquetas especificas de datos como coordenadas de graficos y valores numericos.

## Layout & Spacing
El sistema sigue una **grid de baseline de 4px** para mantener alineacion matematica. Utiliza una **grid fluida de 12 columnas** para el area de contenido principal, con barra lateral fija de 260px. En tablet, la barra lateral colapsa a 72px (solo iconos). En mobile, layout de una columna con 16px de margen.

## Elevation & Depth
Evita sombras pesadas en favor de **Capas Tonicas** y **Borders de Bajo Contraste**. La profundidad se establece principalmente por cambios de color de fondo. Para modales, sombra muy suave: `0px 4px 20px rgba(15, 23, 42, 0.08)`.

## Shapes
Mantener **Suaves (4px - 12px radius)** para apariencia profesional y sistematica. Radio principal para botones e inputs: 4px. Contenedores mayores: 8px.

## Components
- **Buttons**: Primary con fondo teal y texto blanco. Ghost con texto teal sin fondo.
- **Sidebar**: Fondo navy oscuro (`#0f172a`). Items activos con barra vertical teal.
- **Cards**: Fondo blanco con 1px border (`#e2e8f0`). Sin sombra normal, sombra suave en hover.
- **Data Tables**: Sin zebra striping, usar border-bottom sutil (`1px solid #f1f5f9`).
- **Input Fields**: 1px border con 4px radius. Focus con 2px teal ring.
- **KPI Metrics**: `headline-md` para valor, `label-mono` para descripcion. Tendencias ↑ en teal, ↓ en naranja-rojo.
