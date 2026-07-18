# AIMS Development Guide

## 1. Environment

Recommended versions:

- Python 3.11+
- Node.js 20+
- npm 10+
- SQLite 3+

## 2. Backend Setup

Create virtual environment:

```bash
python -m venv venv
```

Activate environment and install dependencies:

```bash
pip install -r requirements.txt
```

Run backend:

```bash
uvicorn backend.main:app --reload
```

## 3. Frontend Setup

Enter frontend directory:

```bash
cd frontend
```

Install packages:

```bash
npm install
```

Start development server:

```bash
npm run dev
```

## 4. Environment Variables

Use `.env` for local configuration.

Required:

```env