# CyberSight ASM - Authentication & Authorization Module

Module 1 of the CyberSight Attack Surface Management Platform. Implements a complete authentication system with RBAC.

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
uvicorn app.main:app --reload --port 8000
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

## Features

### Authentication
- User registration with email verification
- Secure login with JWT tokens
- Forgot password with email reset link
- Password change for authenticated users

### RBAC Roles
| Role | Permissions |
|------|------------|
| Admin | Full access, user management |
| Threat Analyst | Full IOC management |
| SOC Analyst | View and search data |
| Viewer | Read-only access |

### Admin Dashboard
- List all users with search
- Change user roles
- Activate/Deactivate users
- Delete users

## Folder Structure

```
Threatfusion/
├── backend/
│   ├── app/
│   │   ├── config.py          # Environment settings
│   │   ├── database.py        # MongoDB connection
│   │   ├── main.py            # FastAPI app entry
│   │   ├── models/user.py     # User model & roles
│   │   ├── schemas/user.py    # Pydantic schemas
│   │   ├── routes/            # API routes
│   │   ├── services/          # Business logic
│   │   ├── dependencies/      # Auth dependencies
│   │   └── utils/             # Security & token utils
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── contexts/          # Auth context
│   │   ├── pages/             # Page components
│   │   ├── services/          # API service (axios)
│   │   └── App.jsx            # Router setup
│   ├── package.json
│   └── .env.example
└── README.md
```

## API Endpoints

### Auth (`/api/auth`)
- `POST /register` - Register new user
- `POST /verify-email` - Verify email with token
- `POST /login` - Login
- `POST /forgot-password` - Request password reset
- `POST /reset-password` - Reset password with token

### Users (`/api/users`)
- `GET /me` - Get current user profile
- `PUT /me` - Update profile
- `POST /change-password` - Change password

### Admin (`/api/admin`)
- `GET /users` - List users (Admin only)
- `PUT /users/{id}/role` - Change role (Admin only)
- `PUT /users/{id}/active` - Toggle active (Admin only)
- `DELETE /users/{id}` - Delete user (Admin only)

## First Admin User

Register a user, then manually update their role in MongoDB:

```javascript
db.users.updateOne(
  { email: "your@email.com" },
  { $set: { role: "admin", email_verified: true } }
)
```
