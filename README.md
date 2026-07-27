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
- （可选）已安装 Miniconda / Anaconda

### 1. 安装系统依赖

```bash
sudo apt update
sudo apt install -y git
```

> 如果还未安装 conda，可参考 [Miniconda 官方文档](https://docs.conda.io/projects/miniconda/en/latest/) 安装，或使用系统 Python 3.11+ 配合 venv。

### 2. 克隆项目并配置

```bash
git clone <你的仓库地址> /opt/aims
cd /opt/aims
cp .env.example .env
vi .env   # 编辑环境变量，填入你的 API Key
```

### 3. 创建 Python 环境并安装依赖

**方式 A：使用 conda（推荐，你的服务器已有 conda 环境 `py3127`）**

```bash
# 直接激活你已有的 py3127 环境
conda activate py3127
pip install -r requirements.txt
```

**方式 B：使用 venv（备选）**

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

# 指定其他端口启动
./start.sh 18766
```

### 6. 使用 systemd 开机自启（生产环境推荐）

```bash
sudo cp scripts/linux/aims.service /etc/systemd/system/
sudo vi /etc/systemd/system/aims.service   # 修改 User、API Key、Python 路径等配置
```

> **重要**：`aims.service` 默认已启用 conda 路径（Option A），你只需要：
> 1. 用 `conda run -n py3127 which python` 查看你的 conda python 实际路径
> 2. 将 `ExecStart=` 行中的路径改为实际的 conda python 路径（通常是 `/home/你的用户名/miniconda3/envs/py3127/bin/python`）
> 3. 如果你用的是 venv 而非 conda，则注释掉 Option A，取消注释 Option B

```bash
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

前端构建产物会输出到 `frontend/dist/`，后端 FastAPI 会自动托管静态文件。

> **安全注意**：AIMS 默认监听 `127.0.0.1:18765`（仅本地），外部访问需要通过 Nginx 反向代理 + HTTPS。详见下一步。

### 8. 防火墙配置

如果直接暴露 AIMS 到公网（不推荐），放开内部端口：

```bash
sudo ufw allow 18765/tcp
```

如果使用 Nginx 反向代理（推荐，见下一步），只需要放行 HTTP/HTTPS：

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```

### 9. 配置 Nginx 反向代理 + HTTPS（安全上线）

> **为什么需要这一步？**
> - AIMS 本身没有认证，任何人访问端口就能看到数据
> - 端口 `18765` 绑定在 `127.0.0.1`（仅本地），外部无法直连
> - Nginx 作为前置网关，提供 **HTTPS 加密**、**基础认证**、**防扫描**

#### 9.1 安装 Nginx

```bash
sudo apt update
sudo apt install -y nginx apache2-utils
```

#### 9.2 申请 SSL 证书（Let's Encrypt）

```bash
# 安装 certbot
sudo apt install -y certbot python3-certbot-nginx

# 申请证书（替换 your-domain.com 为你的域名）
sudo certbot --nginx -d your-domain.com
```

> 如果没有域名，可以使用服务器 IP + 自签名证书，或先跳过 HTTPS 直接用 HTTP（不推荐用于生产）。

#### 9.3 配置 Nginx

项目已提供 Nginx 配置模板：

```bash
sudo cp scripts/linux/aims-nginx.conf /etc/nginx/sites-available/aims
sudo vi /etc/nginx/sites-available/aims
```

> **编辑要点**：
> - 将 `server_name` 改为你的域名（或服务器 IP）
> - 如果跳过 HTTPS，删除第一个 `server` 块和第二个 `server` 块中的 SSL 相关行

#### 9.4 启用基础认证（推荐）

```bash
# 创建用户（替换 aims 为你的用户名）
sudo htpasswd -c /etc/nginx/.htpasswd aims
# 会提示输入密码

# 在 aims-nginx.conf 中取消注释以下三行：
# auth_basic           "AIMS - 请输入用户名密码";
# auth_basic_user_file /etc/nginx/.htpasswd;
```

#### 9.5 启用站点并重载

```bash
sudo ln -s /etc/nginx/sites-available/aims /etc/nginx/sites-enabled/
sudo nginx -t          # 测试配置
sudo systemctl reload nginx
```

#### 9.6 访问

```text
https://your-domain.com/          → AIMS 仪表盘（带 HTTPS + 认证）
https://your-domain.com/api/...   → API 接口
```

完成后，你的架构是：

```text
用户 ── HTTPS :443 ──→ Nginx（认证） ── HTTP :18765 ──→ AIMS/FastAPI
                                                            │
                                                    SQLite / 东方财富 API / ...
```

### 目录结构说明

```text
/opt/aims/
├── backend/              FastAPI 后端
├── frontend/             React 前端
├── storage/              SQLite 数据库目录
├── logs/                 运行日志
├── runtime/              PID 文件
├── scripts/
│   ├── linux/
│   │   ├── start-aims.sh    Linux 启动脚本 (端口 18765, 绑定 127.0.0.1)
│   │   ├── stop-aims.sh     Linux 停止脚本
│   │   ├── aims.service     systemd 服务单元
│   │   └── aims-nginx.conf  Nginx 反向代理配置模板
│   └── windows/          Windows 启动/停止脚本
├── start.sh              Linux 启动入口
└── stop.sh               Linux 停止入口
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
