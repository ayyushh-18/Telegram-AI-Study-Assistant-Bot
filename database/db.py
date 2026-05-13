import sqlite3


conn = sqlite3.connect(
    "history.db",
    check_same_thread=False
)

cursor = conn.cursor()


# ---------------- CREATE TABLE ---------------- #

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    command TEXT,
    content TEXT

)
""")

conn.commit()


# ---------------- SAVE HISTORY ---------------- #

def save_history(user_id, command, content):

    cursor.execute(
        "INSERT INTO history (user_id, command, content) VALUES (?, ?, ?)",
        (user_id, command, content)
    )

    conn.commit()


# ---------------- GET HISTORY ---------------- #

def get_history(user_id):

    cursor.execute(
        """
        SELECT command, content
        FROM history
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
        """,
        (user_id,)
    )

    return cursor.fetchall()


# ---------------- CLEAR HISTORY ---------------- #

def clear_history(user_id):

    cursor.execute(
        "DELETE FROM history WHERE user_id=?",
        (user_id,)
    )

    conn.commit()