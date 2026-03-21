# 🏛 AS-Vault Bank

A full-stack banking web application built with HTML/CSS/JS frontend and Python Flask backend.

## 🚀 Live Demo
Coming soon on Render!

## 📁 Project Structure
```
as-vault-bank/
├── index.html        # Frontend (white & gold banking UI)
├── app.py            # Flask backend API
├── database.db       # SQLite database (auto-created on first run)
├── requirements.txt  # Python dependencies
└── README.md
```

## ⚙️ How to Run Locally

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the backend
```bash
python app.py
```
You should see:
```
✅ AS-Vault Bank backend is running!
📡 API available at: http://localhost:5000
```

### 3. Open the frontend
Open `index.html` in your browser.

## 🔌 API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/create-account | Create new account |
| POST | /api/login | Login with PIN |
| GET | /api/accounts | Get all accounts |
| POST | /api/deposit | Deposit money |
| POST | /api/withdraw | Withdraw money |
| GET | /api/transactions/:id | Get transaction history |
| DELETE | /api/delete-account/:id | Delete account |

## 🛠 Tech Stack
- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python Flask
- **Database:** SQLite
- **Deployment:** Render (backend) + GitHub Pages (frontend)

## 👩‍💻 Built by Alisha Bhatti
