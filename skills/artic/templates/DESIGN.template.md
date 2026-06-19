---
version: alpha
name: "{{PROJECT_NAME}}"
description: "{{DESIGN_DESCRIPTION}}"
colors:
  primary: "#1F4FD8"
  secondary: "#465064"
  accent: "#7C3AED"
  surface: "#FFFFFF"
  neutral: "#F6F8FB"
  text: "#111827"
  muted: "#6B7280"
  border: "#DDE3EA"
typography:
  h1:
    fontFamily: Inter
    fontSize: 4rem
    fontWeight: 760
    lineHeight: 1.05
    letterSpacing: "-0.04em"
  h2:
    fontFamily: Inter
    fontSize: 2.5rem
    fontWeight: 720
    lineHeight: 1.12
  h3:
    fontFamily: Inter
    fontSize: 1.5rem
    fontWeight: 680
    lineHeight: 1.25
  body-md:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.65
  caption:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: 500
    lineHeight: 1.45
rounded:
  sm: 6px
  md: 12px
  lg: 20px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  section: 96px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: 12px
  button-secondary:
    backgroundColor: "{colors.secondary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: 12px
  accent-badge:
    backgroundColor: "{colors.accent}"
    textColor: "#FFFFFF"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  form-field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "{spacing.sm}"
  proof-strip:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.muted}"
    rounded: "{rounded.lg}"
    padding: "{spacing.md}"
  divider:
    backgroundColor: "{colors.border}"
    height: 1px
    width: 100%
  muted-panel:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.muted}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
---

## Overview

{{OVERVIEW}}

## Design North Star

{{DESIGN_NORTH_STAR}}

<!-- artic-policy: reference-safety-v1 -->
Reference policy: extract reusable principles only; do not copy logos, trademarks, proprietary illustrations, or exact layouts.

## Colors

Use role-based color tokens. Primary is reserved for the highest-value conversion action. Secondary supports navigation or lower-emphasis actions. Accent is for sparse emphasis only, not a second brand palette.

## Typography

Use a disciplined hierarchy: one h1 per page, h2 for major sections, h3 for cards/features, body-md for readable content, and caption for proof/meta text.

## Layout

Use a mobile-first layout and consistent spacing rhythm. Keep content in a readable container, avoid arbitrary section padding, and make each section answer one user question.

## Page Composition

Recommended homepage sequence: hero with one primary promise, proof immediately near the hero, feature/job sections, trust or comparison section, conversion area, FAQ, and final CTA.

## Visual Hierarchy

Make the primary conversion path visually dominant. Secondary links must be useful but quieter. Avoid competing CTAs, equal-weight cards for unequal ideas, and decorative elements that overpower the message.

## Responsive Behavior

Mobile-first: stack sections, keep one primary CTA visible, preserve readable line lengths, avoid horizontal overflow, and reduce decorative density before reducing content clarity.

## Elevation & Depth

Use subtle depth only where it clarifies hierarchy. Prefer borders, surface contrast, and spacing before heavy shadows.

## Shapes

Use the documented radius scale consistently. Do not mix more than two radius levels inside one section unless the hierarchy requires it.

## Components

Buttons, cards, forms, navigation, proof sections, feature cards, and final CTA blocks must use the tokens above.

## Motion

Use restrained motion to clarify state, progression, or hierarchy. Avoid motion that delays conversion, distracts from content, or creates accessibility issues.

## Accessibility

Target WCAG AA contrast, visible keyboard focus, semantic buttons/links, labeled form controls, and plain-language validation copy.

## Anti-Patterns

Do not use generic gradient blobs, random glassmorphism, off-token colors, multiple primary CTAs in one viewport, low-contrast muted copy, centered long paragraphs, or exact reference layouts.

## Do's and Don'ts

Do follow the Artic reference synthesis. Don't copy a reference site exactly.
