import sqlite3
import pandas as pd
import io

DB_FILE = 'account.db'


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute('''
              CREATE TABLE IF NOT EXISTS ledgers
              (
                  id   INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE
              )
              ''')

    c.execute('''
              CREATE TABLE IF NOT EXISTS records
              (
                  id        INTEGER PRIMARY KEY AUTOINCREMENT,
                  ledger_id INTEGER,
                  date      TEXT,
                  type      TEXT,
                  category  TEXT,
                  amount    REAL,
                  note      TEXT,
                  FOREIGN KEY (ledger_id) REFERENCES ledgers (id)
              )
              ''')

    c.execute('''
              CREATE TABLE IF NOT EXISTS categories
              (
                  id        INTEGER PRIMARY KEY AUTOINCREMENT,
                  ledger_id INTEGER,
                  name      TEXT,
                  UNIQUE (ledger_id, name)
              )
              ''')

    c.execute("SELECT count(*) FROM ledgers")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO ledgers (name) VALUES (?)", ("My Ledger",))

        default_ledger_id = c.lastrowid

        default_cats = ["餐饮", "交通", "购物", "居住", "工资", "娱乐"]

        for cat in default_cats:
            c.execute("INSERT INTO categories (ledger_id, name) VALUES (?, ?)", (default_ledger_id, cat))

    conn.commit()
    conn.close()

def get_ledgers():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name FROM ledgers")
    res = c.fetchall()
    conn.close()
    return res


def add_ledger(name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO ledgers (name) VALUES (?)", (name,))
        new_id = c.lastrowid
        default_cats = ["餐饮", "交通", "工资"]
        for cat in default_cats:
            c.execute("INSERT INTO categories (ledger_id, name) VALUES (?, ?)", (new_id, cat))
        conn.commit()
        success = True
    except:
        success = False
    conn.close()
    return success

def save_record(ledger_id, date, type, category, amount, note):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO records (ledger_id, date, type, category, amount, note) VALUES (?, ?, ?, ?, ?, ?)",
              (ledger_id, date, type, category, amount, note))
    conn.commit()
    conn.close()


def get_all_records(ledger_id):
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query("SELECT * FROM records WHERE ledger_id = ? ORDER BY date DESC",
                               conn, params=(ledger_id,))
    except:
        df = pd.DataFrame(columns=['id', 'ledger_id', 'date', 'type', 'category', 'amount', 'note'])
    conn.close()
    return df


def delete_record(record_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM records WHERE id=?", (record_id,))
    rows = c.rowcount
    conn.commit()
    conn.close()
    return rows > 0


def get_summary(df):
    if df.empty:
        return 0.0, 0.0, 0.0
    inc = df[df['type'] == '收入']['amount'].sum()
    exp = df[df['type'] == '支出']['amount'].sum()
    bal = inc - exp
    return inc, exp, bal

def get_categories(ledger_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name FROM categories WHERE ledger_id = ?", (ledger_id,))
    cats = [row[0] for row in c.fetchall()]
    conn.close()
    return cats


def add_category(ledger_id, name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO categories (ledger_id, name) VALUES (?, ?)", (ledger_id, name))
        conn.commit()
        success = True
    except:
        success = False
    conn.close()
    return success


def delete_category(ledger_id, name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM categories WHERE ledger_id=? AND name=?", (ledger_id, name))
    conn.commit()
    conn.close()

def get_records_by_date_range(ledger_id, start_date, end_date):
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT * FROM records WHERE ledger_id = ? AND date BETWEEN ? AND ? ORDER BY date DESC"
    df = pd.read_sql_query(query, conn, params=(ledger_id, start_date, end_date))
    conn.close()
    return df


def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()


def delete_ledger(ledger_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT count(*) FROM ledgers")
    count = c.fetchone()[0]
    if count <= 1:
        conn.close()
        return False, "❌ 无法删除：系统中必须至少保留一个账本！"

    try:
        c.execute("DELETE FROM records WHERE ledger_id=?", (ledger_id,))
        c.execute("DELETE FROM categories WHERE ledger_id=?", (ledger_id,))
        c.execute("DELETE FROM ledgers WHERE id=?", (ledger_id,))

        conn.commit()
        success = True
        msg = "✅ 账本及所有数据已删除"
    except Exception as e:
        success = False
        msg = f"❌ 删除失败: {str(e)}"

    conn.close()
    return success, msg