import sqlite3
from datetime import datetime

DB_NAME = 'accounting.db'

def connect():
    return sqlite3.connect(DB_NAME)

def create_tables():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            password TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT CHECK(type IN ('income', 'expense')) NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount INTEGER NOT NULL,
            date TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            description TEXT,
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')

    conn.commit()
    conn.close()

def insert_user(fullname, password, phone):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (fullname, password, phone) VALUES (?, ?, ?)', (fullname, password, phone))
    conn.commit()
    conn.close()

def check_user():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('SELECT id, fullname, password, phone FROM users')
    users = cursor.fetchall()
    conn.close()
    return [{'id': u[0], 'fullname': u[1], 'password': u[2], 'phone': u[3]} for u in users]

def add_category(name, type_):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO categories (name, type) VALUES (?, ?)', (name, type_))
    conn.commit()
    conn.close()

def add_account(name):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO accounts (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()

def add_transaction(amount, date, category_id, account_id, description=''):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (amount, date, category_id, account_id, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (amount, date, category_id, account_id, description))
    conn.commit()
    conn.close()

def get_categories(type_=None):
    conn = connect()
    cursor = conn.cursor()
    if type_:
        cursor.execute('SELECT id, name FROM categories WHERE type = ?', (type_,))
    else:
        cursor.execute('SELECT id, name FROM categories')
    result = cursor.fetchall()
    conn.close()
    return result

def get_accounts():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM accounts')
    result = cursor.fetchall()
    conn.close()
    return result

def get_transactions():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.id, t.amount, t.date, c.name, a.name, t.description
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        JOIN accounts a ON t.account_id = a.id
        ORDER BY t.date DESC
    ''')
    result = cursor.fetchall()
    conn.close()
    return result

def get_user_fullname(id):
    conn = sqlite3.connect("accounting.db")
    cursor = conn.cursor()
    cursor.execute("SELECT fullname FROM users WHERE id = ?", (id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "به شما"

def get_user_id_by_phone(phone):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE phone = ?", (phone,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None
