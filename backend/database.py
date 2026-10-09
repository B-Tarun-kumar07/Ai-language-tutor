import sqlite3
from pathlib import Path


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_PATH = Path(__file__).parent / "language_tutor.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)

    # Allows us to access rows like dictionaries
    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():

    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            word TEXT NOT NULL,

            reading TEXT,

            romaji TEXT,

            meaning TEXT,

            part_of_speech TEXT,

            role TEXT,

            target_language TEXT NOT NULL,

            known_language TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(
                word,
                target_language,
                known_language
            )
        )
        """
    )

    connection.commit()

    connection.close()


# ============================================================
# SAVE VOCABULARY
# ============================================================

def save_vocabulary(word_data):

    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT OR IGNORE INTO vocabulary
        (
            word,
            reading,
            romaji,
            meaning,
            part_of_speech,
            role,
            target_language,
            known_language
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            word_data["word"],
            word_data.get("reading", ""),
            word_data.get("romaji", ""),
            word_data.get("meaning", ""),
            word_data.get("part_of_speech", ""),
            word_data.get("role", ""),
            word_data["target_language"],
            word_data["known_language"],
        ),
    )

    connection.commit()

    word_id = cursor.lastrowid

    # If the word already existed,
    # INSERT OR IGNORE returns 0.
    # So retrieve the existing ID.
    if word_id == 0:

        existing = connection.execute(
            """
            SELECT id
            FROM vocabulary
            WHERE word = ?
            AND target_language = ?
            AND known_language = ?
            """,
            (
                word_data["word"],
                word_data["target_language"],
                word_data["known_language"],
            ),
        ).fetchone()

        if existing:
            word_id = existing["id"]

    connection.close()

    return word_id


# ============================================================
# GET VOCABULARY
# ============================================================

def get_vocabulary(
    target_language="Japanese",
    known_language="English",
):

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            word,
            reading,
            romaji,
            meaning,
            part_of_speech,
            role,
            target_language,
            known_language,
            created_at
        FROM vocabulary
        WHERE target_language = ?
        AND known_language = ?
        ORDER BY created_at DESC
        """,
        (
            target_language,
            known_language,
        ),
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


# ============================================================
# DELETE VOCABULARY
# ============================================================

def delete_vocabulary(word_id):

    connection = get_connection()

    cursor = connection.execute(
        """
        DELETE FROM vocabulary
        WHERE id = ?
        """,
        (word_id,),
    )

    connection.commit()

    deleted = cursor.rowcount > 0

    connection.close()

    return deleted