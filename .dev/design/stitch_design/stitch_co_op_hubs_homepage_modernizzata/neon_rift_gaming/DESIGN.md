```markdown
# Design System Document

## 1. Overview & Creative North Star: "The Neon Archive"

This design system is a bespoke framework crafted for a high-end gaming library experience. Moving away from the rigid, sterile grids of traditional marketplaces, "The Neon Archive" treats game discovery as an editorial journey. 

**The Creative North Star: The Digital Curator.**
The interface should feel like a premium, dark-mode gallery where games are showcased as art pieces. We break the "template" look by utilizing deep tonal layering, intentional asymmetry in content density, and high-contrast typography. The visual language balances the "hard" technical nature of gaming with "soft" organic glassmorphism, creating a tactile atmosphere that feels deep, mysterious, and intentional.

---

## 2. Colors: Depth Through Darkness

The palette is rooted in deep purples and ink-blacks, utilizing vibrant neon accents to categorize gameplay types without overwhelming the eye.

### Palette Strategy
*   **Base Tone (`#161024`):** The primary background. It is not pure black, but a "Deep Space" violet that retains enough saturation to feel premium.
*   **The Neon Accents:** 
    *   **Secondary (`#00eefc`):** Reserved for "Local" play. High energy, high visibility.
    *   **Tertiary (`#2ae500`):** Reserved for "Online" play. A sharp, digital green.
*   **The "No-Line" Rule:** 1px solid borders are strictly prohibited for sectioning. Structural boundaries must be defined solely through background shifts (e.g., a `surface-container-low` card sitting on a `surface` background).
*   **Glass & Gradient Rule:** Navigation bars and floating panels must utilize `surface-variant` with a `24px` backdrop-blur and 60% opacity. For primary CTAs, use a linear gradient from `primary` (#c7bfff) to `primary_container` (#8d7fff) at a 135-degree angle to provide a "lit from within" soul.

---

## 3. Typography: Editorial Precision

The typography system juxtaposes the aggressive, modern geometry of **Space Grotesk** with the utilitarian precision of **Inter** (for body) and **JetBrains Mono** (for technical data).

*   **Display & Headlines (Space Grotesk):** Large, tight tracking. These should feel like magazine mastheads. Use `display-lg` for hero titles to establish an immediate sense of scale.
*   **Body (Inter):** High readability. We use `body-md` for game descriptions to ensure the user can consume information without fatigue.
*   **Labels (JetBrains Mono):** Used for technical metadata (e.g., player counts, version numbers). This adds a "developer-shell" aesthetic that resonates with gaming culture.

---

## 4. Elevation & Depth: Tonal Layering

In this design system, height is not achieved with lines, but through light and transparency.

*   **The Layering Principle:** Depth is conveyed by "stacking" surface tiers.
    *   **Level 0:** `surface` (The canvas)
    *   **Level 1:** `surface-container-low` (Navigation rails, background sections)
    *   **Level 2:** `surface-container` (Standard game cards)
    *   **Level 3:** `surface-container-high` (Hover states, active modals)
*   **Ambient Shadows:** Floating elements (modals/tooltips) use an extra-diffused shadow: `box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4)`. The shadow should feel like a soft glow of "absence" rather than a hard drop-shadow.
*   **The "Ghost Border" Fallback:** If a divider is required for accessibility, use the `outline_variant` token at **15% opacity**. It should be felt, not seen.
*   **Glassmorphism:** Use `surface_container_low` at 70% opacity with a `Blur(16px)` for sidebars to allow the deep purple hues of the background to bleed through, softening the interface.

---

## 5. Components: Functional Elegance

### Buttons
*   **Primary:** High-contrast `primary` background with `on_primary` text. Always use `md` (12px) rounded corners.
*   **Secondary/Neon:** Use the `secondary` or `tertiary` tokens for category-specific actions.
*   **Interaction:** On hover, primary buttons should scale to 102% with a subtle `surface_tint` outer glow.

### Game Cards
*   **Structure:** No borders. Use `surface_container` for the card body. 
*   **Glass Header:** The top area of a card (holding categories) should use a subtle glass gradient to overlay the game artwork.
*   **Spacing:** Use `spacing-4` (1rem) for internal padding to give elements room to breathe.

### Chips (Category Tags)
*   **Design:** Pill-shaped (`rounded-full`). 
*   **Logic:** "Local" tags use `secondary_container` with `on_secondary_container` text. "Online" tags use `tertiary_container` with `on_tertiary_container`.

### Input Fields
*   **Style:** `surface_container_lowest` backgrounds with a "Ghost Border" that illuminates to `primary` color on focus. No labels inside the box; use `label-md` (JetBrains Mono) above the field for an "engineering" feel.

### Navigation Rails
*   **Layout:** Vertical, high-blur glassmorphism. Avoid traditional "Top Nav" bars where possible to maximize vertical immersion for game lists.

---

## 6. Do’s and Don’ts

### Do
*   **Do** use asymmetrical margins (e.g., wider left padding than right) in hero sections to create a sense of movement.
*   **Do** rely on the 12px (`md`) corner radius for all containers to maintain a "friendly-tech" aesthetic.
*   **Do** use the Spacing Scale religiously to ensure vertical rhythm without the need for dividers.

### Don’t
*   **Don't** use 100% opaque, high-contrast borders. This breaks the "Neon Archive" immersion.
*   **Don't** use standard "Drop Shadows." If it needs to float, it needs a soft, ambient glow or tonal shift.
*   **Don't** clutter the UI with icons. Let the high-end typography and neon color-coding do the heavy lifting.
*   **Don't** use pure white (`#FFFFFF`) for body text. Use `on_surface_variant` (`#c8c4d7`) to reduce eye strain against the dark background.

---

*This design system is a living document intended to evolve with the platform. Always prioritize the "feel" of the depth over rigid adherence to a grid.*```