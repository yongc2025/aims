# AIMS

AI Market Intelligence System，AI 驱动的 A 股市场情报采集、沉淀与可视化分析系统。

## 项目定位

AIMS 聚焦于公开市场数据的结构化采集、质量校验、历史存储和仪表盘展示。

目标：

- 使用 AI Agent 采集公开市场信息
- 将 AI 输出标准化为结构化 JSON
- 通过校验流程控制数据质量
- 使用 SQLite 保存历史数据和 Markdown 日报
- 通过 FastAPI 提供后端接口
- 通过 React、Ant Design、ECharts 展示市场仪表盘

AIMS 不提供：

- 自动交易
- 投资建议
- 市场预测

## 技术栈

Backend:

- Python 3.11+
- FastAPI
- Pydantic
- SQLite
- OpenCode compatible LLM API

Frontend:

- React
- TypeScript
- Vite
- Ant Design
- ECharts

## 项目结构

```text
backend/          FastAPI、Agent、LLM、存储和服务层
frontend/         React dashboard
prompts/          AI 采集提示词
docs/             架构、数据模型、Agent 规格和开发文档
scripts/
├── linux/        Linux 启动/停止脚本 (Ubuntu 部署用)
├── windows/      Windows 启动/停止脚本
├── *.py          验收与测试脚本
tests/            后端测试
storage/          本地 SQLite 数据库目录
logs/             运行日志目录
runtime/          PID 文件目录
start.sh          Linux 启动入口
stop.sh           Linux 停止入口
start.bat         Windows 启动入口
stop.bat          Windows 停止入口
```

## 环境变量

复制示例配置：

```bash
cp .env.example .env
```

使用 DeepSeek V4 Flash 时，`.env` 至少需要：

```env
LLM_PROVIDER=opencode
OPENCODE_BASE_URL=https://api.deepseek.com/v1
OPENCODE_API_KEY=你的 API Key
OPENCODE_MODEL=deepseek-v4-flash
DATABASE_URL=sqlite:///storage/aims.db
API_HOST=0.0.0.0
API_PORT=8000
```

如果你的 OpenCode 平台模型名使用免费模型格式，可将 `OPENCODE_MODEL` 改为平台要求的模型 ID。

## 后端启动（本地开发）

在项目根目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -c "from backend.storage.database import init_database; init_database()"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

访问：

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/api/market/health
```

查看进程或停止服务：

```bash
ss -tlnp | grep :8000    # 查看端口占用
lsof -i :8000            # 或使用 lsof
kill <PID>               # 停止进程
```

## 前端启动（本地开发）

另开一个终端：

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

访问：

```text
http://127.0.0.1:5173/
```

## 数据采集

配置好 `.env` 后，可以运行单日采集：

```bash
python -m backend.agents.run_akshare_collector 2026-07-17
```

采集流程：

```text
Prompt
  -> LLM
  -> JSON Parser
  -> Pydantic Validator
  -> Markdown Generator
  -> SQLite Storage
```

## 验证命令

后端语法和测试：

```bash
python -m compileall backend scripts tests
python scripts/test_pipeline.py
python -m pytest
```

前端构建：

```bash
cd frontend
npm run build
```

当前已验证通过：

- 后端编译检查
- 数据库初始化与验收脚本
- pytest 测试
- 前端 production build

## Ubuntu 服务器部署

### 前置要求

- Ubuntu 22.04 LTS 或更新版本
- Python 3.11+
- Git

### 1. 安装系统依赖

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

### 2. 克隆项目并配置

```bash
git clone <你的仓库地址> /opt/aims
cd /opt/aims
cp .env.example .env
vi .env   # 编辑环境变量，填入你的 API Key
```

### 3. 创建虚拟环境并安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 初始化数据库

```bash
python -c "from backend.storage.database import init_database; init_database()"
```

### 5. 使用启动脚本（推荐）

```bash
# 设置执行权限
chmod +x start.sh stop.sh scripts/linux/*.sh

# 启动（默认端口 8000）
./start.sh

# 停止
./stop.sh

# 指定端口启动
./start.sh 8080
```

### 6. 使用 systemd 开机自启（生产环境推荐）

```bash
sudo cp scripts/linux/aims.service /etc/systemd/system/
sudo vi /etc/systemd/system/aims.service   # 修改 User 和 API Key 等配置
sudo systemctl daemon-reload
sudo systemctl enable aims
sudo systemctl start aims

# 查看状态
sudo systemctl status aims

# 查看日志
sudo journalctl -u aims -f
```

### 7. 前端构建

```bash
cd frontend
npm install
npm run build
```

前端构建产物会输出到 `frontend/dist/`，后端 FastAPI 会自动托管静态文件。访问 `http://<服务器IP>:8000/` 即可看到仪表盘。

### 8. 防火墙配置

```bash
# 如果使用 ufw
sudo ufw allow 8000/tcp
sudo ufw reload
```

### 目录结构说明

```text
/opt/aims/
├── backend/         FastAPI 后端
├── frontend/        React 前端
├── storage/         SQLite 数据库目录
├── logs/            运行日志
├── runtime/         PID 文件
├── scripts/
│   ├── linux/       Linux 启动/停止脚本
│   └── windows/     Windows 启动/停止脚本
├── start.sh         Linux 启动入口
└── stop.sh          Linux 停止入口
```

## API 概览

```text
GET /                         应用状态 / 前端页面
GET /api/market/health        market API 健康检查
GET /api/market/{date}        查询指定日期市场数据
GET /api/reports/{date}       查询指定日期 Markdown 日报
GET /api/analysis/margin      两融趋势数据
GET /api/analysis/sentiment   市场情绪趋势
GET /api/analysis/sectors     板块热力图数据
```

## 开发原则

- Data first, analysis later
- AI 输出必须先结构化，再入库
- 无来源、无校验的数据不进入正式表
- 系统用于情报管理和趋势展示，不用于交易决策
