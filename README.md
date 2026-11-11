# CyberSight ASM 

Attack Surface Management platform to automate external asset discovery, service fingerprinting,
vulnerability identification, technology detection, and security reporting.

## Tech Stack

**Backend:** Python FastAPI, MongoDB (Motor), JWT, Passlib (bcrypt)  
**Frontend:** React + Vite, Tailwind CSS, React Router, Axios

## Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB running locally or a connection string
- Gmail account with App Password (for email verification)

## Setup

### 1. Clone & Navigate

```bash
cd Threatfusion
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
```

Edit `.env` with your MongoDB URI, JWT secret, and Gmail SMTP credentials.

Run the backend:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/api/docs

### 3. Frontend

```bash
cd frontend
npm install
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
```

Run the frontend:

```bash
npm run dev
```

App available at: http://localhost:5173

