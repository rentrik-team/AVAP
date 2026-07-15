# Frontend Architecture

---

# Purpose

This document defines the complete frontend architecture for the Automated Vulnerability Assessment Platform (AVAP).

It serves as the authoritative guide for frontend implementation, ensuring architectural consistency, maintainability, scalability, security, and an enterprise-grade user experience.

This document defines:

- Frontend architecture
- Folder structure
- State management
- API communication
- Security guidelines
- Component architecture
- UI/UX standards
- Routing
- Error handling
- Performance standards
- Accessibility
- Design system
- Deployment architecture

It does **not** define backend behavior.

---

# Primary Goals

The frontend should be:

- Enterprise-grade
- Production-ready
- Highly maintainable
- Secure
- Modular
- Responsive
- Accessible
- Fast
- Easy to extend

The frontend should resemble modern enterprise SaaS platforms rather than consumer websites.

Reference quality:

- Linear
- Vercel
- Stripe Dashboard
- Notion
- Datadog
- Sentry
- Retool
- Grafana
- Prisma Data Platform

---

# Deployment Architecture

Frontend and backend are deployed independently.

```
Browser
      ↓
Next.js Frontend
      ↓
HTTPS REST API
      ↓
FastAPI Backend
```

Frontend must never assume:

- localhost
- same origin
- same deployment
- shared filesystem
- shared sessions

All communication occurs through HTTPS REST APIs.

No direct database communication.

---

# Technology Stack

Framework

- Next.js (App Router)

Language

- TypeScript

Styling

- TailwindCSS

Component Library

- shadcn/ui

Icons

- Lucide React

Charts

- Recharts

Tables

- TanStack Table

Forms

- React Hook Form

Validation

- Zod

State Management

- Zustand

Server State

- TanStack Query

Animations

- Framer Motion

Notifications

- Sonner

Theme

- next-themes

HTTP Client

- Axios

Date Handling

- date-fns

File Download

- Browser Blob API

---

# Architectural Principles

Follow:

- Component Driven Architecture
- Feature Based Organization
- Atomic UI Composition
- Separation of Concerns

Never:

- Mix API logic inside UI components
- Place business logic inside pages
- Call APIs directly from JSX
- Duplicate state
- Duplicate API code

---

# Directory Structure

```
app/

components/

features/

hooks/

services/

api/

lib/

providers/

store/

types/

schemas/

constants/

styles/

utils/

config/

assets/

public/

middleware.ts
```

Feature folders should own:

- pages
- components
- hooks
- api
- schemas

Global reusable code belongs only in shared directories.

---

# API Layer

Frontend never calls Axios directly.

Architecture:

```
Component

↓

Feature Hook

↓

Service

↓

API Client

↓

Axios Instance

↓

Backend
```

Example

```
Dashboard

↓

useDashboard()

↓

DashboardService

↓

apiClient

↓

Backend
```

---

# API Client

Single centralized client.

Responsibilities:

- Base URL
- Timeouts
- Retry policy
- Request interceptors
- Response interceptors
- Error normalization

Never create multiple Axios instances unless absolutely necessary.

---

# Environment Variables

Never hardcode URLs.

Use:

```
NEXT_PUBLIC_API_BASE_URL
```

Example

```
https://api.example.com
```

Never assume localhost.

---

# API Versioning

Always call versioned APIs.

Example

```
/api/v1/dashboard
```

Never hardcode version strings throughout the application.

---

# Server State

Use TanStack Query.

Benefits:

- caching
- stale handling
- retries
- optimistic updates
- pagination
- invalidation

Never duplicate server state inside Zustand.

---

# Global State

Use Zustand only for:

- Theme
- Sidebar state
- User preferences
- UI settings
- Temporary workflow state

Never store API responses inside Zustand.

---

# Forms

Every form:

React Hook Form

+

Zod

Never use uncontrolled validation.

---

# Error Handling

Errors should be normalized.

Never expose backend stack traces.

User sees:

- readable message
- retry button
- support reference if available

---

# Authentication (Future)

No implementation now.

Frontend should remain architecture-ready.

Authentication provider will plug into:

```
providers/

middleware

route guards

auth hooks
```

Do not scaffold authentication now.

---

# Routing

Use App Router.

Feature routes only.

Avoid deeply nested routes.

---

# Loading States

Every page should provide:

- Skeleton loader
- Empty state
- Error state
- Success state

Never leave blank screens.

---

# Design System

## Design Language

Premium Enterprise SaaS.

Characteristics:

- Clean
- Spacious
- Elegant
- Minimal
- Data-centric
- Professional

Avoid:

- Excessive gradients
- Loud colors
- Heavy glassmorphism
- Cartoon UI

---

# Design Inspiration

Primary inspiration:

The attached dashboard design.

Additional inspiration:

- Linear
- Vercel
- Stripe
- Sentry
- Notion
- Arc Browser

---

# Color Palette

Primary

Purple

Secondary

Indigo

Background

Warm Light Gray

Surface

White

Success

Green

Warning

Amber

Error

Red

Information

Blue

Dark Mode

Neutral Slate

Accent colors should only highlight important actions.

---

# Component Style

Components should use:

- 16–24px radius
- subtle shadows
- soft elevation
- premium spacing
- smooth hover animations
- minimal borders

No overly sharp corners.

---

# Typography

Use:

Inter

Hierarchy:

Display

Heading

Title

Body

Caption

Maintain strong visual hierarchy.

---

# Dashboard Principles

Dashboard is the core product.

It should prioritize:

- Risk overview
- Scan status
- Assets
- Vulnerabilities
- AI recommendations
- Reports

Information density should remain high while preserving clarity.

---

# UX Principles

Fast interactions.

Minimal clicks.

Clear navigation.

Progressive disclosure.

Consistent spacing.

Predictable interactions.

No unnecessary modals.

Keyboard friendly.

---

# Animations

Framer Motion only.

Animations should be:

- smooth
- subtle
- meaningful

No decorative animations.

---

# Accessibility

Meet WCAG AA.

Requirements:

- keyboard navigation
- visible focus
- ARIA labels
- semantic HTML
- sufficient contrast
- screen reader compatibility

---

# Responsive Design

Desktop first.

Support:

Desktop

Laptop

Tablet

Mobile

Dashboard should gracefully collapse.

No horizontal scrolling.

---

# Security

Never:

- store secrets
- expose tokens
- trust client validation
- expose stack traces

Always:

- validate API responses
- sanitize rendered content
- use HTTPS
- use CSP-compatible code
- avoid dangerouslySetInnerHTML

---

# Performance

Lazy loading

Dynamic imports

Image optimization

Code splitting

Memoization where justified

Route prefetching

Virtualization for large tables

Avoid unnecessary renders.

---

# API Consumption Rules

Every endpoint should have:

Service

↓

Hook

↓

Component

Never bypass layers.

---

# Testing

Future:

Vitest

React Testing Library

Playwright

---

# Code Standards

Small components.

Small hooks.

Reusable UI.

No duplicate code.

Meaningful naming.

Strict TypeScript.

No any.

---

# Future Enhancements

Authentication

RBAC

Notifications

Real-time updates

Dark mode improvements

Offline support

PWA

These are architectural placeholders only.

No implementation at this stage.

---

# General Rule

The frontend should feel like a premium cybersecurity platform rather than a traditional admin dashboard.

Every screen should communicate:

Professionalism

Trust

Security

Clarity

Speed

Consistency