# AIMS Data Schema

## Principle

AI output must be structured JSON first. Markdown is generated for human reading.

## Version

Current schema version: 1.0

## Core Entities

### Market Daily

- date
- index data
- turnover
- market statistics
- limit up/down statistics

### Sector Data

- sector name
- sector type
- limit up count
- ranking

### Limit Chain Stock

- stock code
- stock name
- chain days
- industry
- reason

### News Event

- title
- date
- source
- category

## Validation Rules

- Missing data uses explicit null or 未公开披露
- No estimated values
- Units must be preserved
- Source should be recorded
