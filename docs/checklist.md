# AIMS Quality Checklist

## AI Output Validation

- All required sections exist
- No missing mandatory fields
- Source information included
- No subjective investment opinions

## Before Database Insert

- Schema validation passed
- Date format valid
- Numeric fields are valid numbers
- Units are consistent
- Duplicate records handled

## Data Integrity Rules

- Up + Down + Flat count should be reasonable
- Negative values rejected where invalid
- Missing values use explicit null status
- Failed validation must not enter production tables

## Pipeline

```
AI Response
    ↓
JSON Parser
    ↓
Schema Validator
    ↓
Business Validator
    ↓
Database Insert
```
