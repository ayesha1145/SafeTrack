# 🛰️ SafeTrack – Student Safety & Emergency Response Platform
> A full-stack web application ensuring secure, real-time emergency reporting and student safety management.

SafeTrack is a full-featured, privacy-first safety platform built for instant emergency communication. It connects students and administrators through live alerts, secure authentication, multilingual access (English + Bengali), and data-driven response tracking — enabling faster, smarter crisis management.

## 🚀 Overview
SafeTrack provides an interactive safety system designed to protect students during emergencies. It integrates a **FastAPI backend** for secure data operations with a **React frontend** for real-time alert visualization and management. Students can report incidents, view their alert history, and administrators can oversee live cases — all through one centralized, multilingual dashboard.

## ✨ Core Features
- 🆘 **Emergency Alerts:** Students can instantly send verified alerts with ID, blood group, contact info, and location  
- 🌍 **Multilingual Support:** Full bilingual access (English + Bengali)  
- 🔐 **JWT Authentication:** Secure role-based access for students and admins  
- 🧑‍💻 **Admin Dashboard:** Manage, filter, and resolve active emergencies  
- 🧭 **Real-Time Tracking:** Displays geolocation and timestamps for all alerts  
- 💾 **MongoDB Storage:** Fast, flexible, and reliable NoSQL database  
- 🧩 **Modular APIs:** RESTful, scalable backend routes for users and alerts  
- 🧠 **Privacy Focus:** Built without third-party trackers or analytics  

## 🧠 Tech Stack
| Layer | Technologies |
|--------|---------------|
| **Frontend** | React, JavaScript (ES6), HTML5, CSS3 |
| **Backend** | FastAPI (Python), Uvicorn, REST APIs |
| **Database** | MongoDB (Motor) |
| **Authentication** | JWT Tokens, OAuth2 |
| **Deployment** | Render (Backend), Vercel (Frontend) |
| **Testing** | Python Requests-based Integration Suite |
| **Version Control** | Git + GitHub |

## 🗂️ Folder Structure
SafeTrack/  
├── backend/  
│   ├── server.py — FastAPI backend for alerts and user management  
│   ├── requirements.txt — Backend dependencies  
│   ├── render.yaml — Render deployment configuration  
│   ├── Procfile — Render start command  
│   └── .env — Environment variables for backend configuration  
│  
├── frontend/  
│   ├── public/ — Static files (index.html, favicon)  
│   ├── src/  
│   │   ├── components/ — UI components (forms, alerts, dashboard)  
│   │   ├── hooks/ — Custom React hooks  
│   │   ├── lib/ — Helper utilities for frontend logic  
│   │   ├── App.js — Root application logic  
│   │   └── index.js — Entry point for rendering  
│   ├── package.json — Frontend dependencies  
│   └── .env — Frontend configuration variables  
│  
├── tests/  
│   ├── backend_test.py — Unit and integration tests for API endpoints  
│   ├── test_result.md — Summary of backend test results  
│   └── README.md — Testing documentation and examples  
│  
└── README.md — (This file)

## ⚙️ Installation & Setup
### 1️⃣ Clone the Repository
git clone https://github.com/ayesha1145/SafeTrack.git  
cd SafeTrack

### 2️⃣ Backend Setup
cd backend  
pip install -r requirements.txt  

Create a `.env` file inside the `backend/` folder:
MONGO_URL=your_mongo_connection_string  
DB_NAME=safetrack  
SECRET_KEY=your_secret_key  
CORS_ORIGINS=*  

Run the backend:
uvicorn server:app --reload  

### 3️⃣ Frontend Setup
cd ../frontend  
npm install  
npm start  

Once started, SafeTrack runs locally through your configured API endpoint.

## 🧪 Testing
Run automated backend tests:  
cd tests  
python backend_test.py  

**To view summarized test outputs:**  
Open `tests/test_result.md`.

## 🔑 API Reference
| Endpoint | Method | Description | Auth |
|-----------|--------|-------------|------|
| `/api/status` | GET | Check API health | ❌ |
| `/api/auth/register` | POST | Register new student | ❌ |
| `/api/auth/login` | POST | Authenticate student or admin | ❌ |
| `/api/students/me` | GET | Retrieve current student profile | ✅ |
| `/api/students/me` | PUT | Update student profile | ✅ |
| `/api/alerts` | POST | Create a new emergency alert | ✅ |
| `/api/alerts` | GET | Retrieve all alerts | ✅ |
| `/api/alerts/active` | GET | View active alerts (admin only) | ✅ |
| `/api/alerts/{alert_id}` | PUT | Update alert status | ✅ |

✅ **Auth Required:** Endpoints marked with this icon require a Bearer token in the header (`Authorization: Bearer <token>`).

## ☁️ Deployment Guide
### Backend (Render)
1. Go to Render (https://render.com)  
2. Click **New → Web Service** and connect your GitHub repository  
3. Root Directory → backend  
4. Build Command → pip install -r requirements.txt  
5. Start Command → uvicorn server:app --host 0.0.0.0 --port $PORT  
6. Deploy and verify at your Render URL  

### Frontend (Vercel)
1. Go to Vercel (https://vercel.com)  
2. Import your GitHub repo  
3. Root Directory → frontend  
4. Add environment variable:  
REACT_APP_BACKEND_URL=https://safetrack-backend.onrender.com  
5. Deploy frontend and connect to backend  

## 🔮 Future Enhancements
- Integrate push notifications for emergency alerts  
- Add geofencing and campus safety mapping  
- Include SMS/email alert subscriptions  
- Enhance dashboard with analytics and alert history  

## 💡 Project Highlights
- Clean modular architecture separating backend and frontend logic  
- Secure, authenticated APIs with robust token validation  
- Full multilingual support for accessibility  
- Scalable FastAPI backend and MongoDB data store  
- Automated testing ensures data consistency and API stability  
- Fully deployable on Render (backend) and Vercel (frontend)

## 💬 Contribution Guide
1. Fork the repository  
2. Create a new branch:  
git checkout -b feature-name  
3. Commit your changes:  
git commit -m "feat: describe new feature"  
4. Push to the branch:  
git push origin feature-name  
5. Open a Pull Request  

## 📄 License
This project is open-source under the MIT License.  
Free to use, adapt, and extend for educational and research purposes.


