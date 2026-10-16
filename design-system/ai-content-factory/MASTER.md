# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** AI Content Factory
**Generated:** 2026-10-16 12:09:36
**Category:** E-commerce Luxury

---

## Global Rules

### Color Palette (Solarin Luxury Palette)

| Role | Hex | Name | CSS Variable | Usage |
|------|-----|------|--------------|-------|
| Deep Obsidian Base | `#2C3531` | Dark Slate Charcoal | `--color-base-800` | Background canvas, deep card panels, base surfaces |
| Primary Accent / Jewel | `#116466` | Deep Jewel Teal | `--color-accent-500` / `--color-primary` | Main CTA buttons, active state rings, primary branding |
| Warm Secondary Tone | `#D9B08C` | Sand Bronze Tan | `--color-amber-500` / `--color-secondary-container` | Secondary accents, warm metallic badges, gradient stops |
| Luminous Highlight | `#FFCB9A` | Glowing Peach Apricot | `--color-amber-400` / `--color-secondary` | Warm button hover glow, active badges, highlights |
| High-Contrast Text / Glow | `#D1E8E2` | Luminous Ice Mint | `--color-base-200` / `--color-on-surface` | Primary legible text, laser borders, crisp button text |

**Color Notes:** High-contrast sci-fi luxury palette inspired by Sirin Labs Solarin interface. Jewel teal base with glowing ice mint and warm peach highlights over deep slate obsidian.

### Typography

- **Heading Font:** Plus Jakarta Sans / Share Tech Mono
- **Body Font:** Inter / JetBrains Mono
- **Mood:** sci-fi luxury, precision tech, editorial dark, futuristic
- **Google Fonts:** [Plus Jakarta Sans + JetBrains Mono](https://fonts.google.com/share?selection.family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@500;600;700;800)

### Spacing Variables

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | `4px` / `0.25rem` | Tight gaps |
| `--space-sm` | `8px` / `0.5rem` | Icon gaps, inline spacing |
| `--space-md` | `16px` / `1rem` | Standard padding |
| `--space-lg` | `24px` / `1.5rem` | Section padding |
| `--space-xl` | `32px` / `2rem` | Large gaps |
| `--space-2xl` | `48px` / `3rem` | Section margins |
| `--space-3xl` | `64px` / `4rem` | Hero padding |

### Shadow Depths

| Level | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.4)` | Subtle lift |
| `--shadow-md` | `0 4px 16px rgba(17,100,102,0.45)` | Primary jewel teal buttons |
| `--shadow-lg` | `0 6px 24px rgba(25,130,132,0.55)` | Hover state glow |
| `--shadow-warm` | `0 4px 16px rgba(217,176,140,0.35)` | Warm peach / bronze buttons |

---

## Component Specs

### Buttons

```css
/* Primary Action Button (Jewel Teal #116466 + Mint #D1E8E2) */
.btn-primary {
  background: linear-gradient(135deg, #116466 0%, #0d4e50 100%);
  color: #d1e8e2;
  border: 1px solid rgba(209, 232, 226, 0.30);
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 600;
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4), 0 4px 16px rgba(17, 100, 102, 0.45);
  cursor: pointer;
}

.btn-primary:hover {
  background: linear-gradient(135deg, #198284 0%, #116466 100%);
  color: #ffffff;
  border-color: rgba(209, 232, 226, 0.65);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4), 0 6px 24px rgba(25, 130, 132, 0.55), 0 0 16px rgba(209, 232, 226, 0.35);
  transform: translateY(-1px);
}

/* Secondary Button (Obsidian Glass #2C3531 + Mint Border) */
.btn-secondary {
  background: rgba(44, 53, 49, 0.55);
  color: #d1e8e2;
  border: 1px solid rgba(209, 232, 226, 0.16);
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 500;
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.btn-secondary:hover {
  background: rgba(17, 100, 102, 0.30);
  border-color: rgba(255, 203, 154, 0.45);
  color: #ffcb9a;
  box-shadow: 0 0 16px rgba(17, 100, 102, 0.28);
}

/* Warm Accent Button (Glowing Peach #FFCB9A + Bronze #D9B08C) */
.btn-warm {
  background: linear-gradient(135deg, #ffcb9a 0%, #d9b08c 100%);
  color: #2c3531;
  font-weight: 600;
  border-radius: 12px;
  padding: 10px 20px;
  box-shadow: 0 2px 12px rgba(217, 176, 140, 0.35);
  cursor: pointer;
}
```

### Cards

```css
.card {
  background: #FAFAF9;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-md);
  transition: all 200ms ease;
  cursor: pointer;
}

.card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}
```

### Inputs

```css
.input {
  padding: 12px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 200ms ease;
}

.input:focus {
  border-color: #1C1917;
  outline: none;
  box-shadow: 0 0 0 3px #1C191720;
}
```

### Modals

```css
.modal-overlay {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: var(--shadow-xl);
  max-width: 500px;
  width: 90%;
}
```

---

## Style Guidelines

**Style:** Liquid Glass

**Keywords:** Flowing glass, morphing, smooth transitions, fluid effects, translucent, animated blur, iridescent, chromatic aberration

**Best For:** Premium SaaS, high-end e-commerce, creative platforms, branding experiences, luxury portfolios

**Key Effects:** Morphing elements (SVG/CSS), fluid animations (400-600ms curves), dynamic blur (backdrop-filter), color transitions

### Page Pattern

**Pattern Name:** Horizontal Scroll Journey

- **Conversion Strategy:** Immersive product discovery. High engagement. Keep navigation visible.
28,Bento Grid Showcase,bento,  grid,  features,  modular,  apple-style,  showcase", 1. Hero, 2. Bento Grid (Key Features), 3. Detail Cards, 4. Tech Specs, 5. CTA, Floating Action Button or Bottom of Grid, Card backgrounds: #F5F5F7 or Glass. Icons: Vibrant brand colors. Text: Dark., Hover card scale (1.02), video inside cards, tilt effect, staggered reveal, Scannable value props. High information density without clutter. Mobile stack.
29,Interactive 3D Configurator,3d,  configurator,  customizer,  interactive,  product", 1. Hero (Configurator), 2. Feature Highlight (synced), 3. Price/Specs, 4. Purchase, Inside Configurator UI + Sticky Bottom Bar, Neutral studio background. Product: Realistic materials. UI: Minimal overlay., Real-time rendering, material swap animation, camera rotate/zoom, light reflection, Increases ownership feeling. 360 view reduces return rates. Direct add-to-cart.
30,AI-Driven Dynamic Landing,ai,  dynamic,  personalized,  adaptive,  generative", 1. Prompt/Input Hero, 2. Generated Result Preview, 3. How it Works, 4. Value Prop, Input Field (Hero) + 'Try it' Buttons, Adaptive to user input. Dark mode for compute feel. Neon accents., Typing text effects, shimmering generation loaders, morphing layouts, Immediate value demonstration. 'Show, don't tell'. Low friction start.
- **CTA Placement:** Floating Sticky CTA or End of Horizontal Track
- **Section Order:** 1. Intro (Vertical), 2. The Journey (Horizontal Track), 3. Detail Reveal, 4. Vertical Footer

---

## Anti-Patterns (Do NOT Use)

- ❌ Vibrant & Block-based
- ❌ Playful colors

### Additional Forbidden Patterns

- ❌ **Emojis as icons** — Use SVG icons (Heroicons, Lucide, Simple Icons)
- ❌ **Missing cursor:pointer** — All clickable elements must have cursor:pointer
- ❌ **Layout-shifting hovers** — Avoid scale transforms that shift layout
- ❌ **Low contrast text** — Maintain 4.5:1 minimum contrast ratio
- ❌ **Instant state changes** — Always use transitions (150-300ms)
- ❌ **Invisible focus states** — Focus states must be visible for a11y

---

## Pre-Delivery Checklist

Before delivering any UI code, verify:

- [ ] No emojis used as icons (use SVG instead)
- [ ] All icons from consistent icon set (Heroicons/Lucide)
- [ ] `cursor-pointer` on all clickable elements
- [ ] Hover states with smooth transitions (150-300ms)
- [ ] Light mode: text contrast 4.5:1 minimum
- [ ] Focus states visible for keyboard navigation
- [ ] `prefers-reduced-motion` respected
- [ ] Responsive: 375px, 768px, 1024px, 1440px
- [ ] No content hidden behind fixed navbars
- [ ] No horizontal scroll on mobile
