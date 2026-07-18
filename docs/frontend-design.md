# AIMS Frontend Design Specification

## Overview

AIMS frontend is designed as a fintech-style AI market intelligence dashboard.

Design goal:

- Professional financial terminal feeling
- Technology-oriented visual style
- Responsive support for PC and mobile
- Data-driven visualization

## Technology Stack

- React + TypeScript
- Vite
- Ant Design
- Tailwind CSS
- Apache ECharts
- echarts-for-react
- Framer Motion

## Design Language

Theme:

- Dark background
- Financial terminal style
- Data visualization first
- Minimal decoration

Keywords:

- AI
- Market Intelligence
- Data Flow
- Real-time Monitoring

## Chart Standard

All charts must be dynamically generated from data.

Do not use static images.

Architecture:

```
Database
  ↓
FastAPI API
  ↓
React Data Layer
  ↓
ECharts Rendering
```

## Core Charts

### Market Trend

- Index trend
- Turnover trend
- Sentiment trend

### Financing Balance

Source:

margin_balance_weekly

Display:
