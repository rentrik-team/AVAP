# AVAP Design System

## Document Purpose

This document defines the visual language, interaction standards, component styling, and user experience rules for the Automated Vulnerability Assessment Platform (AVAP).

It is the authoritative frontend design specification for all AVAP interfaces.

The design system exists to ensure that every page, feature, component, chart, table, form, and interaction feels like part of one cohesive enterprise cybersecurity product.

This document defines:

- visual direction
- design principles
- color system
- typography
- spacing
- layout
- surfaces
- elevation
- borders
- component styling
- data visualization
- cybersecurity severity representation
- interaction states
- motion
- responsive behavior
- accessibility
- design implementation rules

This document does not define:

- backend architecture
- API behavior
- business logic
- database behavior
- authentication implementation
- RBAC implementation

Frontend architecture and API integration rules belong in `frontend.md`.

---

# 1. Product Design Direction

AVAP must feel like a premium enterprise cybersecurity platform.

The interface should communicate:

- trust
- control
- technical precision
- security
- clarity
- operational awareness
- professionalism

The product must not resemble:

- a generic admin template
- a college dashboard
- a crypto dashboard
- a gaming interface
- a consumer social application
- a neon "hacker" interface
- a terminal-themed cybersecurity stereotype

The visual language should combine:

- premium SaaS minimalism
- soft modern surfaces
- strong information hierarchy
- restrained purple accents
- high-quality data visualization
- cybersecurity-specific status semantics
- dense information presented without visual clutter

The primary visual inspiration is the provided dashboard reference.

The reference establishes the following direction:

- soft neutral background
- elevated white surfaces
- large rounded containers
- purple primary accent
- restrained gradients
- comfortable spacing
- subtle depth
- lightweight navigation
- elegant chart presentation

AVAP must adapt this visual language for enterprise security workflows.

Do not directly copy the reference layout or consumer-oriented components.

The design direction is:

> Soft Premium Enterprise Security UI

---

# 2. Core Design Principles

## 2.1 Clarity Before Decoration

Security information must be immediately understandable.

Never sacrifice:

- vulnerability readability
- risk visibility
- scan state clarity
- error comprehension
- data comparison

for visual decoration.

A beautiful interface that obscures security state is a failed interface.

---

## 2.2 Premium Through Restraint

Premium design is achieved through:

- spacing
- typography
- proportion
- alignment
- subtle elevation
- consistent motion
- carefully controlled color

Premium does not mean adding more effects.

Avoid excessive:

- gradients
- shadows
- blur
- glassmorphism
- animations
- glowing borders
- decorative backgrounds

---

## 2.3 Purple Is Brand, Not Risk

Purple is AVAP's primary product accent.

Purple is used for:

- primary actions
- active navigation
- selected controls
- focus indicators
- branded data series
- neutral product highlights

Purple must never replace security severity semantics.

For example:

- Critical remains red
- High remains orange-red
- Medium remains amber
- Low remains blue
- Informational remains neutral

A Critical vulnerability must never appear purple merely to match the brand.

---

## 2.4 Data First

AVAP is a data-intensive application.

The interface must prioritize:

- scan state
- risk score
- risk level
- severity
- affected assets
- services
- vulnerabilities
- remediation availability
- report state
- audit context

Decorative content must never dominate operational data.

---

## 2.5 Progressive Disclosure

Do not display every available field at once.

Use:

- summaries
- expandable sections
- detail panels
- drawers
- dedicated detail pages
- tooltips where appropriate

Users should see the most important information first and inspect deeper context when required.

---

## 2.6 Predictable Interaction

The same action must behave consistently throughout AVAP.

Examples:

- destructive actions use the same confirmation pattern
- filters use the same interaction model
- pagination behaves consistently
- tables use consistent selection states
- errors follow the same presentation pattern
- loading states follow the same visual language

Do not create feature-specific interaction patterns without a genuine UX reason.

---

# 3. Design Tokens

Design values must be implemented as reusable tokens.

Do not scatter arbitrary values throughout components.

The preferred token hierarchy is:

```text
Primitive Tokens
        ↓
Semantic Tokens
        ↓
Component Tokens
```

Example:

```text
purple-600
    ↓
primary
    ↓
button-primary-background
```

Components should primarily consume semantic tokens.

---

# 4. Color System

## 4.1 Primary Brand Palette

The AVAP brand palette is based on a refined violet-purple family inspired by the provided dashboard reference.

| Token | Hex | Purpose |
|---|---|---|
| `purple-50` | `#F7F3FF` | Very subtle selected backgrounds |
| `purple-100` | `#EEE5FF` | Soft accent surfaces |
| `purple-200` | `#DDCCFF` | Decorative accent |
| `purple-300` | `#C4A5FF` | Secondary visual emphasis |
| `purple-400` | `#A875F5` | Hover highlights |
| `purple-500` | `#8B5CF6` | Primary accent |
| `purple-600` | `#7C3AED` | Primary action |
| `purple-700` | `#6D28D9` | Primary action hover |
| `purple-800` | `#5B21B6` | Strong brand emphasis |
| `purple-900` | `#4C1D95` | Deep brand tone |

Primary semantic token:

```text
primary = purple-600
```

Primary hover:

```text
primary-hover = purple-700
```

Primary subtle:

```text
primary-subtle = purple-50
```

Primary foreground:

```text
primary-foreground = #FFFFFF
```

---

## 4.2 Primary Gradient

Gradients are allowed only for high-value branded emphasis.

Primary gradient:

```css
linear-gradient(
  135deg,
  #9B5CF6 0%,
  #7C3AED 55%,
  #6D28D9 100%
)
```

Approved uses:

- primary CTA where additional prominence is justified
- compact brand accents
- selected dashboard visualization
- premium summary highlight
- active progress indication

Do not use the gradient for:

- every button
- tables
- full page backgrounds
- long text containers
- destructive actions
- severity badges

A page should normally contain no more than a few prominent gradient surfaces.

---

## 4.3 Neutral Light Palette

| Token | Hex | Purpose |
|---|---|---|
| `neutral-0` | `#FFFFFF` | Primary surface |
| `neutral-25` | `#FCFCFD` | Elevated clean surface |
| `neutral-50` | `#F8F9FC` | Secondary surface |
| `neutral-100` | `#F1F3F8` | Page background |
| `neutral-200` | `#E6E8F0` | Borders |
| `neutral-300` | `#D2D6E1` | Strong border |
| `neutral-400` | `#9CA3B5` | Disabled text |
| `neutral-500` | `#6B7280` | Secondary text |
| `neutral-600` | `#4B5563` | Supporting text |
| `neutral-700` | `#374151` | Strong text |
| `neutral-800` | `#1F2937` | Heading text |
| `neutral-900` | `#111827` | Primary text |
| `neutral-950` | `#080B12` | Maximum contrast |

Recommended light theme:

```text
page-background = neutral-100
surface = neutral-0
surface-secondary = neutral-50
border = neutral-200
text-primary = neutral-900
text-secondary = neutral-600
text-muted = neutral-500
```

The page background should have a very subtle cool lavender undertone.

Avoid pure white as the entire application background.

White should primarily represent elevated surfaces.

---

## 4.4 Dark Palette

Dark mode must be designed deliberately.

Do not simply invert light theme colors.

| Token | Hex | Purpose |
|---|---|---|
| `dark-950` | `#090A0F` | Main background |
| `dark-900` | `#0F1118` | Secondary background |
| `dark-850` | `#141720` | Primary surface |
| `dark-800` | `#1A1E29` | Elevated surface |
| `dark-700` | `#252A38` | Borders |
| `dark-600` | `#343A4A` | Strong borders |
| `dark-400` | `#8D94A5` | Muted text |
| `dark-300` | `#B2B8C5` | Secondary text |
| `dark-100` | `#EAECF2` | Primary text |
| `dark-50` | `#F7F8FA` | Maximum contrast |

Recommended dark theme:

```text
page-background = dark-950
surface = dark-850
surface-secondary = dark-900
surface-elevated = dark-800
border = dark-700
text-primary = dark-100
text-secondary = dark-300
text-muted = dark-400
```

Dark mode must maintain the premium soft-surface language without producing excessive glow.

Purple accents should be slightly brighter in dark mode where contrast requires it.

---

# 5. Security Severity Color System

Security severity colors are semantic and immutable.

They must remain visually consistent throughout AVAP.

## Critical

```text
foreground: #B42318
background: #FEF3F2
border: #FECDCA
strong: #D92D20
```

Dark mode:

```text
foreground: #FDA29B
background: rgba(217, 45, 32, 0.12)
border: rgba(240, 68, 56, 0.30)
```

---

## High

```text
foreground: #C4320A
background: #FFF4ED
border: #FFD6AE
strong: #E04F16
```

Dark mode:

```text
foreground: #FDB022
background: rgba(224, 79, 22, 0.12)
border: rgba(247, 144, 9, 0.30)
```

---

## Medium

```text
foreground: #B54708
background: #FFFAEB
border: #FEDF89
strong: #F79009
```

Dark mode:

```text
foreground: #FEC84B
background: rgba(247, 144, 9, 0.12)
border: rgba(247, 144, 9, 0.28)
```

---

## Low

```text
foreground: #175CD3
background: #EFF8FF
border: #B2DDFF
strong: #2E90FA
```

Dark mode:

```text
foreground: #84CAFF
background: rgba(46, 144, 250, 0.12)
border: rgba(46, 144, 250, 0.28)
```

---

## Informational

```text
foreground: #475467
background: #F2F4F7
border: #D0D5DD
strong: #667085
```

Dark mode:

```text
foreground: #B2B8C5
background: rgba(152, 162, 179, 0.10)
border: rgba(152, 162, 179, 0.24)
```

---

# 6. Operational Status Colors

Operational status must remain separate from vulnerability severity.

## Success

```text
foreground: #027A48
background: #ECFDF3
strong: #12B76A
```

## Warning

```text
foreground: #B54708
background: #FFFAEB
strong: #F79009
```

## Error

```text
foreground: #B42318
background: #FEF3F2
strong: #F04438
```

## Information

```text
foreground: #175CD3
background: #EFF8FF
strong: #2E90FA
```

## Neutral

```text
foreground: #475467
background: #F2F4F7
strong: #667085
```

Scan status colors must be mapped deliberately.

Example:

| Scan Status | Semantic Color |
|---|---|
| Pending | Neutral |
| Running | Information |
| Completed | Success |
| Failed | Error |
| Cancelled | Warning |

Do not derive scan status colors from risk severity.

---

# 7. Typography

## Primary Typeface

Use:

```text
Inter
```

Preferred loading method:

```text
next/font
```

Do not load the font through arbitrary third-party runtime scripts.

Fallback:

```css
font-family:
  Inter,
  ui-sans-serif,
  system-ui,
  -apple-system,
  BlinkMacSystemFont,
  "Segoe UI",
  sans-serif;
```

---

## Typography Scale

### Display Large

```text
font-size: 48px
line-height: 56px
font-weight: 650
letter-spacing: -0.035em
```

Use rarely.

---

### Display

```text
font-size: 40px
line-height: 48px
font-weight: 650
letter-spacing: -0.03em
```

---

### Heading 1

```text
font-size: 32px
line-height: 40px
font-weight: 650
letter-spacing: -0.025em
```

---

### Heading 2

```text
font-size: 24px
line-height: 32px
font-weight: 650
letter-spacing: -0.02em
```

---

### Heading 3

```text
font-size: 20px
line-height: 28px
font-weight: 600
letter-spacing: -0.015em
```

---

### Title

```text
font-size: 16px
line-height: 24px
font-weight: 600
```

---

### Body

```text
font-size: 14px
line-height: 22px
font-weight: 400
```

---

### Body Small

```text
font-size: 13px
line-height: 20px
font-weight: 400
```

---

### Caption

```text
font-size: 12px
line-height: 18px
font-weight: 500
```

---

### Micro

```text
font-size: 11px
line-height: 16px
font-weight: 550
letter-spacing: 0.01em
```

Use Micro text only for:

- compact metadata
- chart annotations
- table secondary information

Never use Micro for primary information.

---

## Numeric Typography

Risk scores, counts, CVSS values, ports, percentages, and large dashboard metrics should use tabular numbers.

```css
font-variant-numeric: tabular-nums;
```

This prevents layout movement when numeric values change.

---

## Text Rules

Avoid excessive uppercase.

Uppercase is allowed for:

- compact status labels
- very small category indicators
- protocol identifiers

Do not write entire headings in uppercase.

Do not use font weight as the only method of establishing hierarchy.

Use:

- size
- spacing
- color
- weight

together.

---

# 8. Spacing System

Use a 4px base spacing system.

| Token | Value |
|---|---|
| `space-0` | 0 |
| `space-1` | 4px |
| `space-2` | 8px |
| `space-3` | 12px |
| `space-4` | 16px |
| `space-5` | 20px |
| `space-6` | 24px |
| `space-8` | 32px |
| `space-10` | 40px |
| `space-12` | 48px |
| `space-16` | 64px |
| `space-20` | 80px |
| `space-24` | 96px |

Do not introduce arbitrary values such as:

```text
17px
23px
29px
37px
```

unless technically required.

---

## Page Spacing

Desktop:

```text
horizontal padding: 32px
vertical padding: 28–32px
```

Large desktop:

```text
horizontal padding: 40px
```

Tablet:

```text
horizontal padding: 24px
```

Mobile:

```text
horizontal padding: 16px
```

---

## Section Spacing

Between major page sections:

```text
32px
```

Between related content groups:

```text
24px
```

Between component title and body:

```text
16px
```

Between compact related fields:

```text
8–12px
```

---

# 9. Border Radius

The reference dashboard uses strongly rounded surfaces.

AVAP should preserve the softness while slightly reducing consumer-style exaggeration.

| Token | Value | Usage |
|---|---|---|
| `radius-xs` | 6px | Compact tags |
| `radius-sm` | 8px | Small controls |
| `radius-md` | 12px | Inputs and buttons |
| `radius-lg` | 16px | Cards |
| `radius-xl` | 20px | Major dashboard cards |
| `radius-2xl` | 24px | Hero surfaces |
| `radius-full` | 9999px | Pills and avatars |

Default component radius:

```text
12px
```

Default card radius:

```text
16px
```

Dashboard feature cards may use:

```text
20px
```

Do not make every component pill-shaped.

---

# 10. Borders

Default border:

```text
1px solid semantic-border
```

Light theme:

```text
#E6E8F0
```

Dark theme:

```text
#252A38
```

Borders should remain subtle.

Do not use thick borders for normal hierarchy.

Security severity borders may use their semantic color tokens.

Selected states may use:

```text
primary border
+
subtle primary background
```

---

# 11. Elevation and Shadows

AVAP uses soft elevation.

## Shadow XS

```css
0 1px 2px rgba(16, 24, 40, 0.04)
```

Use for:

- inputs
- compact controls

---

## Shadow SM

```css
0 1px 3px rgba(16, 24, 40, 0.06),
0 1px 2px rgba(16, 24, 40, 0.03)
```

Use for:

- cards
- navigation

---

## Shadow MD

```css
0 8px 24px rgba(36, 24, 64, 0.08)
```

Use for:

- dropdowns
- floating panels
- popovers

---

## Shadow LG

```css
0 20px 50px rgba(36, 24, 64, 0.12)
```

Use sparingly for:

- dialogs
- major overlays

Do not use heavy black shadows.

Do not stack multiple dramatic shadows.

Dark mode elevation should rely more on surface differentiation and borders than shadows.

---

# 12. Application Shell

The primary application shell should contain:

```text
Sidebar
    +
Main Workspace
```

Optional page-level header belongs inside the main workspace.

The global shell should not use a large traditional website navbar.

AVAP is an operational application.

---

## Sidebar

Desktop expanded width:

```text
248px
```

Desktop collapsed width:

```text
72px
```

Sidebar characteristics:

- soft elevated surface
- visually separated from workspace
- rounded internal active states
- clear iconography
- compact section grouping
- smooth collapse transition

Recommended navigation hierarchy (scan-centric — implemented in
`constants/navigation.ts`):

```text
Overview

Operations
- Targets
- Scans
- Assets

Security
- Findings
- Vulnerabilities

Outputs
- Reports
- Audit Events
```

Risk and AI Remediation are deliberately not primary destinations: risk is
calculated and displayed on a scan's detail page (the workflow hub) and
platform-wide as Findings, and AI remediation is generated from a
finding's remediation sheet. Legacy `/risk` redirects to `/findings`.

Do not add future modules to navigation.

Do not add Authentication, RBAC, Users, Settings, Notifications, or other unavailable product capabilities.

Active navigation:

```text
primary-subtle background
primary foreground
medium weight
```

The active state should use a soft purple surface.

Avoid a large solid purple sidebar.

---

# 13. Page Header

Every primary page should have a consistent page header.

Structure:

```text
Title
Supporting description

Optional metadata
        +
Page actions
```

Example:

```text
Vulnerabilities

Review normalized vulnerabilities discovered
across assessed assets.

                    [Filters] [Export] [Primary Action]
```

Only show actions that exist in the backend.

Do not design fake actions.

Page title should normally use `Heading 1` or `Heading 2` depending on shell density.

---

# 14. Cards

Cards are a major visual element.

Default card:

```text
background: surface
border: subtle
radius: 16px
shadow: SM
padding: 24px
```

Dashboard feature card:

```text
radius: 20px
padding: 24px
```

Card structure:

```text
Header
    ↓
Primary Content
    ↓
Optional Footer
```

Card headers may contain:

- title
- description
- status
- action menu

Do not place unrelated information inside one card merely to reduce page length.

---

## Metric Cards

Metric cards should display:

```text
Label

Primary Metric

Context / Trend / Secondary Metric
```

Example:

```text
Overall Risk

8.7
Critical

12 high-risk assets
```

Risk score and risk level must remain distinct fields.

Do not visually imply that severity and risk are interchangeable.

---

# 15. Buttons

## Button Sizes

### Small

```text
height: 32px
horizontal padding: 12px
radius: 8px
```

### Default

```text
height: 40px
horizontal padding: 16px
radius: 10–12px
```

### Large

```text
height: 48px
horizontal padding: 20px
radius: 12px
```

---

## Primary Button

Use for the page's primary action.

Style:

```text
primary background or approved primary gradient
white foreground
subtle purple shadow
```

Hover:

```text
slightly darker
translateY(-1px) only where motion is appropriate
```

Active:

```text
translateY(0)
```

Do not place multiple primary buttons next to each other.

---

## Secondary Button

Style:

```text
white/surface background
neutral border
primary or strong neutral text
```

---

## Ghost Button

Use for:

- compact toolbar actions
- icon actions
- secondary navigation actions

No permanent border.

---

## Destructive Button

Always use semantic red.

Never use purple for destructive actions.

Destructive actions must not visually resemble primary positive actions.

---

## Icon Button

Minimum interactive target:

```text
40 × 40px
```

Compact table contexts may use:

```text
32 × 32px
```

only when surrounding spacing preserves accessibility.

Every icon-only button requires an accessible label.

---

# 16. Inputs

Default input:

```text
height: 40–44px
radius: 12px
background: surface
border: neutral
```

Focus:

```text
primary border
+
subtle primary focus ring
```

Recommended focus ring:

```css
0 0 0 3px rgba(124, 58, 237, 0.14)
```

Input states:

- default
- hover
- focus
- filled
- disabled
- error

Error states use semantic error colors.

Do not remove focus outlines without an accessible replacement.

---

# 17. Search

Search should follow the soft pill-inspired visual direction of the reference dashboard without becoming excessively rounded.

Recommended:

```text
height: 44px
radius: 14px
```

Structure:

```text
Search Icon
Input
Optional Shortcut Hint
Optional Clear Button
```

Search placeholder text should identify the searchable domain.

Good:

```text
Search assets by IP or hostname
```

Poor:

```text
Search something
```

---

# 18. Selects and Filters

Filters should use consistent controls.

Preferred pattern:

```text
Filter Button
    ↓
Popover / Sheet
    ↓
Explicit Filter Controls
```

Active filters should be visible as removable filter chips.

Example:

```text
Severity: Critical ×
Status: Completed ×
```

Provide:

```text
Clear all
```

when multiple filters are active.

Do not hide active filtering state.

---

# 19. Tables

Tables are critical to AVAP.

Use TanStack Table for complex tables.

Tables must prioritize readability over decorative styling.

Default table structure:

```text
Table Header
Rows
Pagination / Result Count
```

Table header:

```text
12–13px
medium weight
muted foreground
```

Rows:

```text
minimum height: 52px
```

Use subtle row separators.

Avoid fully boxed spreadsheet-style cells.

---

## Table Hover

Hover should use:

```text
neutral-50
```

or:

```text
primary-subtle at very low intensity
```

Do not animate entire rows dramatically.

---

## Table Selection

Selected row:

```text
primary-subtle background
subtle primary border indicator
```

---

## Table Density

Default density:

```text
comfortable
```

Do not begin with a compact enterprise mode.

Future user-selectable density may be considered later.

---

## Table Cell Rules

Primary identifier:

```text
strong text
```

Secondary information:

```text
muted body-small
```

Use monospace selectively for:

- IP addresses
- CVEs
- ports where combined with protocol
- technical identifiers
- UUIDs when displayed

Recommended monospace font:

```text
JetBrains Mono
```

Do not use monospace for normal body content.

---

# 20. Status Badges

Status badges use:

```text
height: 24–28px
radius: full
horizontal padding: 8–10px
```

Structure:

```text
Optional Status Dot
Label
```

Examples:

```text
● Running
● Completed
● Failed
```

Badge colors must follow semantic status rules.

Do not use random colors for badges.

---

# 21. Severity Badges

Severity badges are standardized.

Allowed labels:

```text
Critical
High
Medium
Low
Informational
```

Do not abbreviate severity labels in normal tables.

Charts may use compact labels where space requires it.

The badge must use the security severity color system defined in this document.

---

# 22. Risk Score Presentation

Risk score is numeric.

Risk level is categorical.

They must remain distinguishable.

Recommended presentation:

```text
8.7
Critical
```

or:

```text
8.7 / 10    [Critical]
```

Do not display:

```text
Critical 8.7%
```

Risk score is not a percentage.

Use one decimal place unless backend semantics require additional precision.

Never calculate risk in the frontend.

Display backend-provided deterministic risk values.

---

# 23. Charts

Use Recharts.

Charts should follow the premium minimal visual language.

Chart principles:

- minimal grid lines
- restrained axes
- readable tooltips
- no unnecessary legends
- semantic color use
- accessible labels
- meaningful empty states

---

## Risk Charts

Risk visualizations must use risk-level semantic colors.

Do not use a purple-only gradient to represent:

```text
Informational → Critical
```

Purple may represent a neutral aggregate series such as:

```text
Overall Risk Trend
```

if individual severity levels are not being encoded.

---

## Severity Distribution

Recommended visualization:

- donut chart
- horizontal stacked bar
- compact bar chart

Use fixed severity ordering:

```text
Critical
High
Medium
Low
Informational
```

Do not dynamically reorder severity levels based on count.

This preserves visual recognition.

---

## Tooltips

Chart tooltips should use:

```text
surface
border
radius: 12px
shadow: MD
```

Display exact values.

Do not rely only on chart geometry.

---

## Chart Animation

Initial chart animation:

```text
200–400ms
```

Updates should be subtle.

Disable or reduce animation when the user prefers reduced motion.

---

# 24. Empty States

Every data view requires a designed empty state.

An empty state contains:

```text
Icon or restrained illustration

Title

Explanation

Optional valid action
```

Example:

```text
No scans yet

Create a scan to begin assessing a validated target.

[Create Scan]
```

Only display an action if the backend supports it.

Do not create fake CTA flows.

Empty states must distinguish:

```text
No data exists
```

from:

```text
No results match filters
```

Filtered empty state example:

```text
No vulnerabilities match these filters.

Clear or adjust the active filters.
```

---

# 25. Loading States

Use skeletons for primary page content.

Skeletons should approximate the final layout.

Do not display a full-page spinner for ordinary data loading.

Use spinner indicators for:

- button actions
- compact asynchronous controls
- short blocking operations

Long-running backend processes such as scans must display their actual persisted status.

Do not keep a frontend spinner active indefinitely to simulate scan execution.

---

# 26. Error States

Errors must be actionable.

Structure:

```text
Clear title

Human-readable explanation

Recovery action where possible

Optional request/reference identifier
```

Example:

```text
Unable to load vulnerabilities

The vulnerability data could not be retrieved.

[Try Again]
```

Do not display:

- stack traces
- raw Axios errors
- SQL details
- backend exception names
- internal paths

---

# 27. Toasts

Use Sonner.

Toasts are appropriate for:

- successful creation
- successful deletion
- report generation confirmation
- action failure
- recoverable background error

Do not use toasts for information the user must carefully review.

Critical risk findings do not belong in ephemeral toasts.

Toast duration should be long enough to read.

Error toasts should not disappear excessively quickly.

---

# 28. Dialogs

Dialogs should be used sparingly.

Appropriate:

- destructive confirmation
- focused short form
- high-impact confirmation

Do not use dialogs for:

- large vulnerability details
- report browsing
- complex workflows
- large tables

Use dedicated pages or drawers where appropriate.

Dialog style:

```text
radius: 20px
shadow: LG
padding: 24px
```

---

# 29. Destructive Confirmation

Destructive actions must require deliberate confirmation.

Structure:

```text
Destructive Action Title

Specific consequence

Resource identity

Cancel
Destructive Action
```

Example:

```text
Delete asset?

This removes the asset and related inventory data according
to the backend deletion behavior.

192.168.1.24

[Cancel] [Delete Asset]
```

Do not use vague confirmations such as:

```text
Are you sure?
```

Do not claim consequences that differ from actual backend behavior.

---

# 30. Drawers and Detail Panels

Use a right-side drawer for contextual inspection where the user should remain on the current page.

Examples:

- quick asset preview
- vulnerability preview
- scan metadata
- audit event inspection

Recommended desktop width:

```text
480–640px
```

Do not force complex information into a narrow drawer.

If the information becomes workflow-heavy, use a dedicated detail page.

---

# 31. Navigation UX

Navigation should remain stable.

Do not dynamically reorder navigation based on usage.

Sidebar groups should remain consistent.

Navigation labels must use domain terminology matching the backend.

Use:

```text
Vulnerabilities
```

not:

```text
Threat Problems
```

Use:

```text
Audit Events
```

not:

```text
Activity History
```

unless the backend/product terminology changes deliberately.

---

# 32. Dashboard Design

The dashboard is AVAP's primary operational overview.

The dashboard should not be a collection of unrelated metric cards.

Recommended hierarchy:

```text
Overall Security Posture

↓

Risk and Vulnerability Overview

↓

Scan Operations

↓

High-Risk Assets / Vulnerabilities

↓

AI Remediation Coverage

↓

Recent Reports / Activity
```

The visual hierarchy should make the most security-relevant information visible first.

---

## Dashboard Hero Summary

The first section should communicate:

- overall risk score
- overall risk level
- critical vulnerability count
- high-risk asset count

Use a large premium summary surface.

Purple may be used for neutral brand emphasis.

Critical/high risk indicators retain severity colors.

Do not use a giant decorative illustration.

---

## Dashboard Metric Cards

Metric cards may include:

- Total Targets
- Total Scans
- Total Assets
- Unique Vulnerabilities
- Critical Vulnerabilities
- Reports Generated

Do not add metrics unsupported by the backend.

---

## Dashboard Layout

Desktop should use a responsive 12-column grid.

Example:

```text
Overall Risk Summary        8 columns
Severity Distribution       4 columns

Top Risk Assets             6 columns
Top Vulnerabilities         6 columns

Scan Activity               8 columns
AI Coverage                  4 columns

Recent Reports              12 columns
```

The exact layout may evolve based on actual data density.

Do not rigidly preserve a layout that harms readability.

---

# 33. Asset UI

Asset pages should prioritize:

```text
IPv4
Hostname
Operating System
Services
Risk
Associated Findings
```

IP addresses should be visually prominent.

Services should use compact structured presentation.

Example:

```text
443 / TCP
HTTPS
nginx 1.24
```

Do not combine service metadata into an unreadable sentence.

---

# 34. Vulnerability UI

Vulnerability pages should prioritize:

```text
Name
CVE
Severity
Risk
Affected Assets
Description
Remediation Availability
```

CVE identifiers should be easy to copy.

Long descriptions must remain readable.

Use constrained line length for prose.

Do not display raw database JSON.

---

# 35. Scan UI

Scan state must be highly visible.

Recommended scan header:

```text
Target
Status
Started At
Completed At
Execution Duration
```

Running scans should have subtle active status motion.

Example:

```text
small pulsing status dot
```

Do not animate the entire card.

Do not fabricate scan progress percentages when the backend does not provide progress.

A `RUNNING` state is not equivalent to `63% complete`.

---

# 36. AI Remediation UI

AI recommendations are advisory.

The UI must communicate this.

Recommended label:

```text
AI-assisted remediation
```

Include appropriate supporting text:

```text
Advisory guidance generated from the current vulnerability
and deterministic risk context.
```

Do not present AI guidance as:

- guaranteed fix
- verified remediation
- deterministic risk result

The UI must never imply that AI calculated the risk score.

Risk and AI guidance should be visually separated.

AI recommendation sections may contain:

```text
Summary
Explanation
Remediation Steps
Validation Steps
Cautions
```

Steps should be displayed as structured lists.

Do not render AI output using `dangerouslySetInnerHTML`.

Do not interpret arbitrary AI HTML.

---

# 37. Report UI

Reports are immutable generated artifacts.

The UI should display:

```text
Report ID
Scan
Format
Risk Snapshot
Generated At
File Size
```

Actions:

```text
Download
Delete
```

Only show backend-supported actions.

Report generation should display a clear pending action state.

Do not fabricate report-generation progress.

Download must use the API download endpoint.

Do not construct filesystem paths in the frontend.

---

# 38. Audit Event UI

Audit Events should feel investigative and precise.

Primary table fields may include:

```text
Occurred At
Event Type
Category
Outcome
Actor Type
Resource Type
Resource ID
```

Audit detail should display safe persisted metadata only.

Do not attempt to infer missing sensitive context.

Do not display audit metadata as an unformatted JSON dump by default.

Render known key/value structures cleanly.

A developer-oriented raw JSON view may only be considered later if product requirements explicitly require it.

---

# 39. Motion System

Motion should communicate:

- state change
- hierarchy
- continuity
- feedback

Default duration tokens:

| Token | Duration |
|---|---|
| `motion-fast` | 120ms |
| `motion-default` | 180ms |
| `motion-slow` | 280ms |
| `motion-emphasis` | 400ms |

Default easing:

```css
cubic-bezier(0.2, 0, 0, 1)
```

Use spring motion only for small interactive UI where appropriate.

Avoid playful bounce.

---

## Approved Motion

- button hover
- sidebar collapse
- drawer entrance
- dialog entrance
- filter chip addition/removal
- card content transition
- chart entrance
- status indicator
- skeleton transition

---

## Prohibited Motion

- constantly floating cards
- excessive parallax
- rotating security icons
- glowing vulnerability rows
- animated backgrounds
- decorative particle systems
- shaking error pages

---

# 40. Reduced Motion

Respect:

```css
prefers-reduced-motion
```

When reduced motion is enabled:

- remove non-essential transforms
- disable decorative transitions
- minimize chart animation
- avoid pulsing effects

Functional state changes must remain understandable without animation.

---

# 41. Responsive Design

AVAP is desktop-first because vulnerability assessment workflows are data-intensive.

However, the interface must remain usable across supported viewport sizes.

## Breakpoint Intent

```text
Mobile:       < 640px
Tablet:       640–1023px
Desktop:      1024–1439px
Large:        >= 1440px
```

Use Tailwind breakpoint conventions where practical.

---

## Desktop

Full sidebar.

Multi-column dashboard.

Full tables.

Rich detail layouts.

---

## Tablet

Collapsible sidebar.

Reduced dashboard columns.

Tables may hide secondary columns.

Critical data must remain visible.

---

## Mobile

Mobile support is for:

- dashboard review
- scan state review
- risk inspection
- vulnerability inspection
- report access

Complex desktop tables should transform deliberately.

Do not simply squeeze a 10-column table into a mobile viewport.

Use:

- responsive cards
- prioritized columns
- horizontal table scrolling only as a controlled last resort

The general application shell must not create page-level accidental horizontal overflow.

---

# 42. Accessibility

AVAP targets WCAG 2.2 AA.

Requirements:

- keyboard navigation
- semantic HTML
- accessible names
- visible focus states
- sufficient contrast
- screen-reader-compatible status text
- form labels
- descriptive errors
- reduced-motion support

Color must never be the only indicator of:

- severity
- status
- error
- selection

Example:

Incorrect:

```text
red dot only
```

Correct:

```text
red indicator + "Critical"
```

---

## Focus

Focus indicators must be clearly visible.

Primary focus ring:

```text
3px low-opacity purple ring
```

Destructive controls may use an error-colored focus ring.

Never globally apply:

```css
outline: none;
```

without an accessible replacement.

---

# 43. Iconography

Use Lucide React.

Icon style:

- stroke-based
- visually consistent
- restrained
- functional

Default sizes:

```text
16px compact
18px default
20px prominent control
24px feature icon
```

Do not mix multiple icon libraries.

Do not use emoji as application icons.

Icons must not replace labels where meaning may be ambiguous.

---

# 44. Copywriting

Product copy should be:

- concise
- professional
- technically accurate
- calm
- actionable

Avoid:

```text
Oops!
Uh oh!
Awesome!
Boom!
You're all set!
Hack detected!
Danger everywhere!
```

Prefer:

```text
Unable to generate report.

The report could not be created for this scan.
Try the operation again.
```

Security products must communicate clearly without unnecessary alarmism.

---

# 45. Date and Time Presentation

Use consistent date formatting.

Recommended display:

```text
14 Jul 2026, 21:42
```

Where relative time improves scanning:

```text
4 minutes ago
```

The exact timestamp should remain accessible through:

- tooltip
- detail view

Do not inconsistently mix multiple date formats.

Frontend formatting must use `date-fns`.

Backend timestamps remain the source of truth.

---

# 46. Numbers and Counts

Large dashboard counts may use compact display:

```text
1.2K
24.8K
```

Exact values should remain available where operationally relevant.

Tables should normally display exact values.

Risk scores:

```text
8.7
```

Percentages:

```text
72.4%
```

Ports:

```text
443/TCP
```

Do not abbreviate CVE identifiers.

---

# 47. Z-Index Scale

Use a controlled z-index scale.

| Layer | Value |
|---|---|
| Base | 0 |
| Raised | 10 |
| Sticky | 20 |
| Dropdown | 40 |
| Overlay | 50 |
| Drawer | 60 |
| Dialog | 70 |
| Toast | 80 |
| Critical System Overlay | 90 |

Do not use arbitrary values such as:

```text
z-index: 999999
```

---

# 48. Component Reuse Rules

Before creating a new component:

1. Check shadcn/ui.
2. Check existing AVAP shared components.
3. Check whether an existing primitive can be composed.
4. Create a new component only when necessary.

Prefer composition.

Do not manually recreate:

- dialogs
- popovers
- dropdown menus
- accessible tabs
- tooltips
- selects

when maintained accessible primitives already exist.

---

# 49. Shared AVAP Components

The frontend should establish reusable domain-aware components where repeated usage is proven.

Expected examples:

```text
SeverityBadge
RiskBadge
RiskScore
ScanStatusBadge
PageHeader
MetricCard
DataTable
EmptyState
ErrorState
LoadingSkeleton
FilterBar
CopyableValue
TechnicalIdentifier
ConfirmDeleteDialog
SectionCard
ChartCard
```

Do not create all components before they are needed.

Build them when actual repeated usage exists.

Avoid premature design-system abstraction.

---

# 50. Security UI Rules

The frontend is an untrusted client.

Never assume UI restrictions provide security.

Do not rely on:

- hidden buttons
- disabled controls
- client-side route restrictions

as backend authorization.

Current AVAP has no authentication or RBAC.

Do not fabricate permission states.

Do not create:

```text
Admin
Super Admin
Viewer
Analyst
```

UI roles.

Do not add role badges.

Do not add fake user profile menus implying authenticated identity.

The visual reference contains a user profile card.

AVAP must **not copy that component at this stage** because user identity does not currently exist in the backend architecture.

---

# 51. API Data Rendering Security

Treat every backend string as untrusted display data.

Never use:

```tsx
dangerouslySetInnerHTML
```

for:

- vulnerability descriptions
- hostnames
- scanner metadata
- AI recommendations
- audit metadata

Render text through React's normal text interpolation.

Do not create a generic HTML renderer for backend content.

If markdown support is introduced in the future, it requires a separate security review and explicit sanitization policy.

---

# 52. Theme Rules

Support:

```text
Light
Dark
System
```

through `next-themes`.

The default should follow system preference unless product requirements explicitly change.

All components must use semantic theme tokens.

Do not write:

```text
bg-white
```

throughout feature code when the semantic intention is:

```text
surface
```

Do not create dark mode by adding isolated `dark:` classes inconsistently across hundreds of components.

Centralize semantic colors through the Tailwind/theme token architecture.

---

# 53. Design Quality Gate

A frontend feature is not visually complete merely because it renders.

Before marking a page complete, verify:

- correct information hierarchy
- consistent spacing
- semantic color usage
- light theme
- dark theme
- loading state
- empty state
- error state
- hover state
- focus state
- disabled state
- responsive behavior
- keyboard navigation
- screen-reader labels
- reduced motion
- no accidental overflow
- no raw API errors
- no fake backend capability
- no duplicated visual pattern
- no arbitrary design token

---

# 54. Prohibited Design Patterns

Do not use:

- neon green hacker themes
- matrix backgrounds
- excessive terminal aesthetics
- cyberpunk visuals
- excessive glassmorphism
- excessive neumorphism
- giant gradient blobs
- glowing card borders
- animated particles
- random dashboard colors
- excessive pill components
- emoji icons
- inconsistent corner radii
- unbounded shadows
- raw JSON as primary UI
- endless modal workflows
- fake charts
- fake metrics
- fabricated progress percentages
- fake user profiles
- fake notifications
- fake roles

---

# 55. Final Design Principle

AVAP should visually communicate:

> A precise, intelligent, premium security operations platform that helps users understand technical risk without overwhelming them.

The design should feel calm even when presenting Critical findings.

Urgency must come from clear semantic hierarchy and accurate security information, not visual chaos.

The provided dashboard reference defines AVAP's softness, spacing, rounded surfaces, and purple brand direction.

AVAP's security domain defines its information hierarchy, severity semantics, technical precision, and operational discipline.

Every frontend implementation must preserve both.