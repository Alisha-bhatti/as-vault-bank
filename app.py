from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Allow frontend to talk to backend

DATABASE = 'database.db'

# ── Database setup ─────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def init_db():
    """Create tables if they don't exist"""
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            account_number TEXT UNIQUE NOT NULL,
            pin_hash TEXT NOT NULL,
            balance REAL DEFAULT 0.0,
            total_deposited REAL DEFAULT 0.0,
            total_withdrawn REAL DEFAULT 0.0,
            created_at TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_number TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL DEFAULT 0.0,
            date TEXT NOT NULL,
            FOREIGN KEY (account_number) REFERENCES accounts(account_number)
        )
    ''')
    conn.commit()
    conn.close()

def hash_pin(pin):
    """Hash PIN securely before storing"""
    return hashlib.sha256(pin.encode()).hexdigest()

def fmt_date():
    return datetime.now().strftime("%b %d, %I:%M %p")

# ── Routes ─────────────────────────────────────────────────────

@app.route('/')
def home():
    return jsonify({"message": "AS-Vault Bank API is running!", "status": "ok"})

# ── Create Account ──────────────────────────────────────────────
@app.route('/api/create-account', methods=['POST'])
def create_account():
    data = request.get_json()
    name = data.get('name', '').strip()
    account_number = data.get('account_number', '').strip()
    pin = data.get('pin', '').strip()

    if not name:
        return jsonify({"error": "Name is required"}), 400
    if not any(c.isalpha() for c in name):
        return jsonify({"error": "Name must contain letters, not just numbers"}), 400
    if len(name) < 2:
        return jsonify({"error": "Name must be at least 2 characters"}), 400
    if not account_number:
        return jsonify({"error": "Account number is required"}), 400
    if len(account_number) < 2:
        return jsonify({"error": "Account number must be at least 2 characters"}), 400
    if not pin or len(pin) != 4 or not pin.isdigit():
        return jsonify({"error": "PIN must be exactly 4 digits"}), 400

    conn = get_db()
    # Check if account number already exists
    existing = conn.execute(
        'SELECT id FROM accounts WHERE account_number = ?', (account_number,)
    ).fetchone()

    if existing:
        conn.close()
        return jsonify({"error": "Account number already exists"}), 400

    # Create the account
    conn.execute('''
        INSERT INTO accounts (name, account_number, pin_hash, balance, total_deposited, total_withdrawn, created_at)
        VALUES (?, ?, ?, 0.0, 0.0, 0.0, ?)
    ''', (name, account_number, hash_pin(pin), fmt_date()))

    # Log the first transaction
    conn.execute('''
        INSERT INTO transactions (account_number, type, description, amount, date)
        VALUES (?, 'created', ?, 0.0, ?)
    ''', (account_number, f'Account opened for {name}', fmt_date()))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Account created successfully!",
        "account": {
            "name": name,
            "account_number": account_number,
            "balance": 0.0
        }
    }), 201

# ── Login ───────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    account_number = data.get('account_number', '').strip()
    pin = data.get('pin', '').strip()

    if not account_number or not pin:
        return jsonify({"error": "Account number and PIN are required"}), 400

    conn = get_db()
    account = conn.execute(
        'SELECT * FROM accounts WHERE account_number = ?', (account_number,)
    ).fetchone()
    conn.close()

    if not account:
        return jsonify({"error": "Account not found"}), 404

    if account['pin_hash'] != hash_pin(pin):
        return jsonify({"error": "Incorrect PIN"}), 401

    return jsonify({
        "message": "Login successful",
        "account": {
            "name": account['name'],
            "account_number": account['account_number'],
            "balance": account['balance'],
            "total_deposited": account['total_deposited'],
            "total_withdrawn": account['total_withdrawn']
        }
    })

# ── Get All Accounts (for selection screen) ─────────────────────
@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    conn = get_db()
    accounts = conn.execute(
        'SELECT name, account_number, balance FROM accounts ORDER BY id DESC'
    ).fetchall()
    conn.close()
    return jsonify([dict(a) for a in accounts])

# ── Get Single Account ──────────────────────────────────────────
@app.route('/api/account/<account_number>', methods=['GET'])
def get_account(account_number):
    conn = get_db()
    account = conn.execute(
        'SELECT * FROM accounts WHERE account_number = ?', (account_number,)
    ).fetchone()
    conn.close()

    if not account:
        return jsonify({"error": "Account not found"}), 404

    return jsonify({
        "name": account['name'],
        "account_number": account['account_number'],
        "balance": account['balance'],
        "total_deposited": account['total_deposited'],
        "total_withdrawn": account['total_withdrawn']
    })

# ── Deposit ─────────────────────────────────────────────────────
@app.route('/api/deposit', methods=['POST'])
def deposit():
    data = request.get_json()
    account_number = data.get('account_number', '').strip()
    amount = data.get('amount', 0)

    if not account_number:
        return jsonify({"error": "Account number is required"}), 400
    if not amount or float(amount) <= 0:
        return jsonify({"error": "Please enter a valid amount"}), 400

    amount = float(amount)
    conn = get_db()
    account = conn.execute(
        'SELECT * FROM accounts WHERE account_number = ?', (account_number,)
    ).fetchone()

    if not account:
        conn.close()
        return jsonify({"error": "Account not found"}), 404

    new_balance = account['balance'] + amount
    new_total_dep = account['total_deposited'] + amount

    conn.execute('''
        UPDATE accounts SET balance = ?, total_deposited = ? WHERE account_number = ?
    ''', (new_balance, new_total_dep, account_number))

    conn.execute('''
        INSERT INTO transactions (account_number, type, description, amount, date)
        VALUES (?, 'deposit', 'Deposit', ?, ?)
    ''', (account_number, amount, fmt_date()))

    conn.commit()
    conn.close()

    return jsonify({
        "message": f"Deposited ₹{amount:.2f} successfully!",
        "new_balance": new_balance
    })

# ── Withdraw ────────────────────────────────────────────────────
@app.route('/api/withdraw', methods=['POST'])
def withdraw():
    data = request.get_json()
    account_number = data.get('account_number', '').strip()
    amount = data.get('amount', 0)

    if not account_number:
        return jsonify({"error": "Account number is required"}), 400
    if not amount or float(amount) <= 0:
        return jsonify({"error": "Please enter a valid amount"}), 400

    amount = float(amount)
    conn = get_db()
    account = conn.execute(
        'SELECT * FROM accounts WHERE account_number = ?', (account_number,)
    ).fetchone()

    if not account:
        conn.close()
        return jsonify({"error": "Account not found"}), 404

    if amount > account['balance']:
        conn.close()
        return jsonify({"error": f"Insufficient funds. Balance: ₹{account['balance']:.2f}"}), 400

    new_balance = account['balance'] - amount
    new_total_wit = account['total_withdrawn'] + amount

    conn.execute('''
        UPDATE accounts SET balance = ?, total_withdrawn = ? WHERE account_number = ?
    ''', (new_balance, new_total_wit, account_number))

    conn.execute('''
        INSERT INTO transactions (account_number, type, description, amount, date)
        VALUES (?, 'withdrawal', 'Withdrawal', ?, ?)
    ''', (account_number, amount, fmt_date()))

    conn.commit()
    conn.close()

    return jsonify({
        "message": f"Withdrew ₹{amount:.2f} successfully!",
        "new_balance": new_balance
    })

# ── Transactions ────────────────────────────────────────────────
@app.route('/api/transactions/<account_number>', methods=['GET'])
def get_transactions(account_number):
    conn = get_db()
    txs = conn.execute('''
        SELECT * FROM transactions WHERE account_number = ? ORDER BY id DESC LIMIT 20
    ''', (account_number,)).fetchall()
    conn.close()
    return jsonify([dict(t) for t in txs])

# ── Delete Account ──────────────────────────────────────────────
@app.route('/api/delete-account/<account_number>', methods=['DELETE'])
def delete_account(account_number):
    conn = get_db()
    account = conn.execute(
        'SELECT id FROM accounts WHERE account_number = ?', (account_number,)
    ).fetchone()

    if not account:
        conn.close()
        return jsonify({"error": "Account not found"}), 404

    conn.execute('DELETE FROM transactions WHERE account_number = ?', (account_number,))
    conn.execute('DELETE FROM accounts WHERE account_number = ?', (account_number,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Account deleted successfully"})

# ── Run ─────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()  # Create tables on startup
    print("✅ AS-Vault Bank backend is running!")
    port = int(os.environ.get('PORT', 5000))
    print(f"📡 API available at port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
