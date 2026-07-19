/**
 * AIMS — AI Market Intelligence System
 * Dark Theme Design Tokens
 *
 * All values are raw primitives; no CSS variables, no runtime generation.
 * Import and use directly for consistent styling across the dashboard.
 */

export const darkTheme = {
  // ---- Colors ----
  colors: {
    // Background
    bg: {
      base: '#050816',
      elevated: '#0a0f23',
      overlay: '#0d1230',
      tooltip: '#111838',
    },

    // Cards & Surfaces
    card: {
      bg: 'rgba(10, 15, 35, 0.85)',
      border: 'rgba(255, 255, 255, 0.06)',
      hoverBorder: 'rgba(0, 212, 255, 0.15)',
    },

    // Glass panels
    glass: {
      bg: 'rgba(10, 15, 35, 0.55)',
      border: 'rgba(255, 255, 255, 0.05)',
    },

    // Borders & Dividers
    border: {
      subtle: 'rgba(255, 255, 255, 0.04)',
      default: 'rgba(255, 255, 255, 0.06)',
      strong: 'rgba(255, 255, 255, 0.10)',
      accent: 'rgba(0, 212, 255, 0.20)',
    },

    // Brand / Primary
    primary: {
      main: '#00D4FF',
      light: '#66E5FF',
      dark: '#00A3CC',
      glow: 'rgba(0, 212, 255, 0.25)',
      faint: 'rgba(0, 212, 255, 0.06)',
    },

    // Semantic: Price Movement
    up: {
      main: '#00E676',
      light: '#69F0AE',
      dark: '#00C853',
      bg: 'rgba(0, 230, 118, 0.10)',
      border: 'rgba(0, 230, 118, 0.20)',
    },

    down: {
      main: '#FF5252',
      light: '#FF8A80',
      dark: '#D32F2F',
      bg: 'rgba(255, 82, 82, 0.10)',
      border: 'rgba(255, 82, 82, 0.20)',
    },

    // Semantic: Warning
    warn: {
      main: '#FFC107',
      light: '#FFD54F',
      dark: '#FFA000',
      bg: 'rgba(255, 193, 7, 0.10)',
      border: 'rgba(255, 193, 7, 0.20)',
    },

    // Semantic: Amber / Secondary Accent
    amber: {
      main: '#FFB454',
      light: '#FFCC80',
      dark: '#F57C00',
      bg: 'rgba(255, 180, 84, 0.10)',
      border: 'rgba(255, 180, 84, 0.20)',
    },

    // Text
    text: {
      primary: '#E0E6F0',
      secondary: '#8892A6',
      tertiary: '#5A6480',
      disabled: '#3A4460',
      inverse: '#050816',
    },

    // Chart Series (for multi-line / multi-bar charts)
    chart: {
      series1: '#00D4FF',
      series2: '#7B61FF',
      series3: '#00E676',
      series4: '#FFB454',
      series5: '#FF5252',
      series6: '#FF4081',
      series7: '#40C4FF',
      series8: '#B2FF59',
      grid: 'rgba(255, 255, 255, 0.04)',
      crosshair: 'rgba(255, 255, 255, 0.10)',
    },
  },

  // ---- Typography ----
  fontSize: {
    xs: '10px',
    sm: '11px',
    base: '12px',
    md: '13px',
    lg: '14px',
    xl: '16px',
    '2xl': '18px',
    '3xl': '22px',
    '4xl': '28px',
    hero: '36px',
  },

  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },

  lineHeight: {
    tight: 1.2,
    normal: 1.5,
    relaxed: 1.7,
  },

  letterSpacing: {
    tighter: '-0.03em',
    tight: '-0.02em',
    normal: '0em',
    wide: '0.04em',
    wider: '0.08em',
  },

  // ---- Spacing Scale (px) ----
  spacing: {
    0: '0px',
    1: '2px',
    2: '4px',
    3: '6px',
    4: '8px',
    5: '12px',
    6: '16px',
    7: '20px',
    8: '24px',
    9: '28px',
    10: '32px',
    11: '40px',
    12: '48px',
    13: '56px',
    14: '64px',
    15: '80px',
    16: '96px',
  },

  // ---- Border Radius ----
  radius: {
    none: '0px',
    xs: '2px',
    sm: '4px',
    md: '6px',
    lg: '8px',
    xl: '10px',
    '2xl': '12px',
    '3xl': '16px',
    full: '9999px',
  },

  // ---- Shadows ----
  shadow: {
    none: 'none',

    // Card shadows
    card: '0 4px 24px rgba(0, 0, 0, 0.40), inset 0 1px 0 rgba(255, 255, 255, 0.03)',
    cardHover:
      '0 4px 32px rgba(0, 0, 0, 0.50), 0 0 0 1px rgba(0, 212, 255, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.04)',

    // Glass
    glass: '0 8px 32px rgba(0, 0, 0, 0.30)',

    // Elevated surfaces
    elevated: '0 8px 40px rgba(0, 0, 0, 0.50)',
    tooltip: '0 4px 16px rgba(0, 0, 0, 0.60), 0 0 0 1px rgba(0, 212, 255, 0.15)',

    // Glow effects
    glowPrimary: '0 0 20px rgba(0, 212, 255, 0.15)',
    glowUp: '0 0 12px rgba(0, 230, 118, 0.20)',
    glowDown: '0 0 12px rgba(255, 82, 82, 0.20)',

    // Dropdown / Popover
    popover: '0 12px 48px rgba(0, 0, 0, 0.60), 0 0 0 1px rgba(255, 255, 255, 0.06)',

    // Inner (inset)
    inner: 'inset 0 1px 3px rgba(0, 0, 0, 0.30)',
  },

  // ---- Z-Index Scale ----
  zIndex: {
    base: 0,
    dropdown: 100,
    sticky: 200,
    overlay: 300,
    modal: 400,
    tooltip: 500,
    toast: 600,
  },

  // ---- Transitions ----
  transition: {
    fast: '0.15s ease',
    normal: '0.2s ease',
    slow: '0.3s ease',
    verySlow: '0.5s ease',
  },

  // ---- Blur ----
  blur: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '20px',
    xl: '24px',
  },
} as const;

// ---- Convenience exports ----
export const { colors, fontSize, fontWeight, lineHeight, letterSpacing, spacing, radius, shadow, zIndex, transition, blur } = darkTheme;
