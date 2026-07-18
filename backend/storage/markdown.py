"""Markdown generator for human readable reports."""


def generate_markdown(data: dict) -> str:
    date = data.get("date", "")

    return f"""# A股行情数据报告

日期：{date}

## 一、指数

数据：

```json
{data.get('index', {})}
```

## 二、市场统计

```json
{data.get('market_statistics', {})}
```

"""
