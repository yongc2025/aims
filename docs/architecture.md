# AIMS Architecture

## Overview

AIMS (AI Market Intelligence System) is an AI-driven A-share market data collection system.

Current phase focuses on:

- AI data collection
- Structured JSON output
- Data validation
- Historical storage
- Markdown report generation

## Data Flow

```
User Input Date
      |
      v
Market Collector Agent
      |
      v
JSON Schema Validation
      |
      v
SQLite Storage
      |
      +---- Markdown Report
      |
      +---- Web API
```

## Technology Stack

Backend:

- Python
- FastAPI
- Pydantic
- SQLite

Frontend:

- React
- Ant Design
- ECharts

LLM:

- OpenCode compatible API

## Development Principle

Data first. Analysis later