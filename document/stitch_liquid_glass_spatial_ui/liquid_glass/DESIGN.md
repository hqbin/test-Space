---
name: Ether Engineer
colors:
  surface: '#f9f9fb'
  surface-dim: '#d9dadc'
  surface-bright: '#f9f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3f5'
  surface-container: '#edeef0'
  surface-container-high: '#e8e8ea'
  surface-container-highest: '#e2e2e4'
  on-surface: '#1a1c1d'
  on-surface-variant: '#424656'
  inverse-surface: '#2f3132'
  inverse-on-surface: '#f0f0f2'
  outline: '#727687'
  outline-variant: '#c2c6d8'
  surface-tint: '#0054d6'
  primary: '#0050cb'
  on-primary: '#ffffff'
  primary-container: '#0066ff'
  on-primary-container: '#f8f7ff'
  inverse-primary: '#b3c5ff'
  secondary: '#4c4aca'
  on-secondary: '#ffffff'
  secondary-container: '#6564e4'
  on-secondary-container: '#fffbff'
  tertiary: '#9a3b00'
  on-tertiary: '#ffffff'
  tertiary-container: '#bb5219'
  on-tertiary-container: '#fff6f3'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae1ff'
  primary-fixed-dim: '#b3c5ff'
  on-primary-fixed: '#001849'
  on-primary-fixed-variant: '#003fa4'
  secondary-fixed: '#e2dfff'
  secondary-fixed-dim: '#c2c1ff'
  on-secondary-fixed: '#0b006b'
  on-secondary-fixed-variant: '#3531b4'
  tertiary-fixed: '#ffdbcd'
  tertiary-fixed-dim: '#ffb595'
  on-tertiary-fixed: '#351000'
  on-tertiary-fixed-variant: '#7c2e00'
  background: '#f9f9fb'
  on-background: '#1a1c1d'
  surface-variant: '#e2e2e4'
  glass-surface: rgba(255, 255, 255, 0.15)
  glass-border-light: rgba(255, 255, 255, 0.6)
  glass-border-dark: rgba(255, 255, 255, 0.2)
  success-indicator: '#22C55E'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '600'
    lineHeight: '1.1'
    letterSpacing: -0.04em
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.03em
  headline-md:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.02em
  body-lg:
    fontFamily: Inter
    fontSize: 17px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: -0.01em
  body-md:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  label-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: '1.2'
    letterSpacing: 0.01em
  caption:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: '1.2'
    letterSpacing: 0.02em
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  unit: 8px
  gutter-grid: 24px
  margin-page: 40px
  padding-card: 32px
  safe-area-top: 64px
---

## Brand & Style
Ether Engineer is a high-performance workspace designed for technical precision and mental clarity. The brand personality is "Advanced Serenity"—it combines the rigorous utility of engineering tools with a sophisticated, ethereal aesthetic. 

The design style is **Glassmorphism**, characterized by extreme backdrop blurs (60px), semi-transparent white surfaces, and subtle light-leak gradients. The UI should feel like a polished glass interface floating over a soft, atmospheric environment. High-key lighting, microscopic border details, and a primary emphasis on legibility and depth create an interface that is both futuristic and calming.

## Colors
The palette is rooted in a bright, neutral foundation (#F9F9FB) enhanced by a vibrant "Electric Blue" primary. Colors are used functionally:
- **Primary (#0066FF):** Actionable items, focus states, and progress indicators.
- **Secondary (#4C4ACA):** Supplemental systems like device management.
- **Tertiary (#9E3D00):** Status alerts such as "Flashing" or "Syncing."
- **Glass Layers:** Utilize semi-transparent white overlays with varying opacities (10-30%) to create depth without introducing new hues. 
- **Surface Gradients:** The background is not a flat color but a radial blend of white and neutral greys to simulate studio lighting.

## Typography
The system relies exclusively on **Inter** to maintain a neutral, utilitarian feel that contrasts with the decorative glass effects. 
- **Tracking:** Headlines use tight negative letter-spacing to appear more compact and "engineered."
- **Hierarchy:** Contrast is established through weight shifts (SemiBold for headers vs. Regular for body) rather than dramatic size changes.
- **Monospace Nuance:** While not the main font, the icons and "command key" labels should feel aligned with a 1:1 aspect ratio aesthetic.

## Layout & Spacing
The layout uses a **Fluid Bento Grid** approach. 
- **Desktop:** A fixed-width sidebar (256px) with a fluid main container that caps at 1200px. Content is organized into a 12-column grid.
- **Mobile:** Sidebar collapses to a 80px rail or bottom bar. The 12-column grid reflows to a single column.
- **Rhythm:** An 8px base unit drives all spacing. Large "page margins" of 40px ensure the glass elements have enough room to breathe against the background gradients.

## Elevation & Depth
Depth is created through **diffused translucency** rather than traditional black shadows.
- **Layer 0 (Background):** Soft radial gradients.
- **Layer 1 (Panels):** 15% white opacity, 60px blur, 1px border.
- **Layer 2 (Cards/Inputs):** 20% white opacity, 60px blur, and dual-toned borders (Light on top/left, subtle dark on bottom/right) to simulate a physical "glass pane" edge.
- **Interactions:** Hover states should increase the opacity to 25% and trigger a slight Y-axis lift (-2px) with an expanded, low-opacity shadow to simulate a "magnet" effect.

## Shapes
The shape language is "Hyper-Rounded." 
- **Large Containers:** Use 2rem (32px) corners to feel like modern hardware (e.g., tablets or monitors).
- **Standard Cards/Buttons:** Use 1rem (16px) corners.
- **Inputs:** Maintain the 1rem (16px) radius for consistency with the primary action buttons.
- **Icons:** Encapsulated in squircle or circular backgrounds with soft tints.

## Components
- **Glass Buttons:** Use a 135-degree linear gradient (White 40% to White 10%) with a backdrop blur of 20px. Borders must be 1px solid white at 30% opacity.
- **Inputs:** Feature a "recessed" look using an inset shadow `inset 0 2px 4px rgba(0,0,0,0.02)`. On focus, the border shifts to Primary blue at 30% opacity with a soft outer glow.
- **Cards:** Must include the "Glass-Card" hover effect where the background brightens and the lift is subtle.
- **List Items:** Use a 0.5px subtle bottom border that disappears on hover, replaced by a 20% white rounded-rect highlight.
- **Indicators:** Status pips (Online/Running) must feature a subtle CSS pulse animation and a matching colored glow (`box-shadow`) to simulate a physical LED.