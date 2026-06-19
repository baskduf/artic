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
  h1: {fontFamily: Inter, fontSize: 4rem, fontWeight: 760, lineHeight: 1.05, letterSpacing: "-0.04em"}
  body-md: {fontFamily: Inter, fontSize: 1rem, fontWeight: 400, lineHeight: 1.65}
rounded: {sm: 6px, md: 12px, lg: 20px}
spacing: {sm: 8px, md: 16px, lg: 24px}
components:
  button-primary: {backgroundColor: "{colors.primary}", textColor: "#FFFFFF", rounded: "{rounded.md}", padding: 12px}
---

## Overview

{{OVERVIEW}}

Reference policy: extract reusable principles only; do not copy logos, trademarks, proprietary illustrations, or exact layouts.

## Colors

Use role-based color tokens.

## Typography

Use a disciplined hierarchy.

## Layout

Use a mobile-first layout and consistent spacing rhythm.

## Elevation & Depth

Use subtle depth only where it clarifies hierarchy.

## Shapes

Use the documented radius scale consistently.

## Components

Buttons, cards, forms, navigation, and proof sections must use the tokens above.

## Do's and Don'ts

Do follow the Artic reference synthesis. Don't copy a reference site exactly.
