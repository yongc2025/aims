# AIMS Data Model Specification

## Overview

AIMS uses structured data storage as the core asset layer.

Principle:

```
AI Collection -> Validation -> Database -> API -> Dashboard
```

## Core Tables

## market_reports

Stores daily AI collected reports.

Fields:

- trade_date
- schema_version
- json_content
- markdown_content
- created_at

## market_sentiment_daily

Stores daily market sentiment statistics.

Fields:

- trade_date
- up_count
- down_count
- limit_up_count
- limit_down_count

## margin_balance_weekly

Stores weekly financing balance data.

Fields:

- week_date
- margin_balance

## sector_daily

Stores industry and concept sector data.
