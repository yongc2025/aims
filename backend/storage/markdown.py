"""Markdown generator for human readable reports."""

import json


def generate_markdown(data: dict) -> str:
    date = data.get("date", "")
    index_data = data.get("shanghai_index") or {}
    market_statistics = data.get("market_statistics") or {}
    limit_chain_stocks = data.get("limit_chain_stocks") or []

    return f"""# A股行情数据报告

日期：{date}

## 一、指数

数据：

```json
{json.dumps(index_data, ensure_ascii=False, indent=2)}
```

## 二、市场统计

```json
{json.dumps(market_statistics, ensure_ascii=False, indent=2)}
```

## 三、连板股票

```json
{json.dumps(limit_chain_stocks[:20], ensure_ascii=False, indent=2)}
```

"""
