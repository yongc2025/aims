# AIMS

# AI Market Intelligence System

AI驱动的A股市场情报系统。

## 项目定位

AIMS 是一个基于 AI Agent 的 A股市场数据采集、沉淀与可视化分析平台。

目标：

- 自动采集公开市场数据
- 标准化保存历史数据
- 生成结构化日报
- 提供金融科技风格驾驶舱

## 产品边界

AIMS 不提供：

- 自动交易
- 投资建议
- 市场预测

AIMS 专注：

- 数据采集
- 数据质量校验
- 情报管理
- 趋势展示

## 系统架构

```
AI Agents
    |
    v
Validator
    |
    v
SQLite Database
    |
    v
FastAPI
    |
    v
React Dashboard
    |
    v
ECharts