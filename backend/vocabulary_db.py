import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "language_tutor.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# =========================================================
# HELPERS
# =========================================================

def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    return any(
        column["name"] == column_name
        for column in columns
    )


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            word TEXT NOT NULL,
            reading TEXT,
            romaji TEXT,
            meaning TEXT,

            part_of_speech TEXT,
            role TEXT,

            learning_language TEXT,
            support_language TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(
                word,
                learning_language,
                support_language
            )
        )
    """)

    connection.commit()

    # -----------------------------------------------------
    # REVIEW STATISTICS
    # -----------------------------------------------------

    if not column_exists(
        cursor,
        "vocabulary",
        "correct_count"
    ):
        cursor.execute("""
            ALTER TABLE vocabulary
            ADD COLUMN correct_count INTEGER DEFAULT 0
        """)

    if not column_exists(
        cursor,
        "vocabulary",
        "wrong_count"
    ):
        cursor.execute("""
            ALTER TABLE vocabulary
            ADD COLUMN wrong_count INTEGER DEFAULT 0
        """)

    if not column_exists(
        cursor,
        "vocabulary",
        "review_count"
    ):
        cursor.execute("""
            ALTER TABLE vocabulary
            ADD COLUMN review_count INTEGER DEFAULT 0
        """)

    if not column_exists(
        cursor,
        "vocabulary",
        "mastery_score"
    ):
        cursor.execute("""
            ALTER TABLE vocabulary
            ADD COLUMN mastery_score REAL DEFAULT 0
        """)

    if not column_exists(
        cursor,
        "vocabulary",
        "last_reviewed"
    ):
        cursor.execute("""
            ALTER TABLE vocabulary
            ADD COLUMN last_reviewed TIMESTAMP
        """)

    # -----------------------------------------------------
    # REVIEWABLE FLAG
    # -----------------------------------------------------

    if not column_exists(
        cursor,
        "vocabulary",
        "reviewable"
    ):
        cursor.execute("""
            ALTER TABLE vocabulary
            ADD COLUMN reviewable INTEGER DEFAULT 0
        """)

    connection.commit()

    # -----------------------------------------------------
    # IMPORTANT:
    #
    # Existing vocabulary that already has a real meaning
    # becomes reviewable.
    #
    # Empty/internal entries remain reviewable = 0.
    # -----------------------------------------------------

    cursor.execute("""
        UPDATE vocabulary
        SET reviewable = 1
        WHERE
            meaning IS NOT NULL
            AND TRIM(meaning) != ''
            AND (
                word IS NOT NULL
                AND TRIM(word) != ''
            )
    """)

    connection.commit()
    connection.close()


# =========================================================
# SAVE VOCABULARY
# =========================================================

def save_vocabulary(
    word,
    reading="",
    romaji="",
    meaning="",
    part_of_speech="",
    role="",
    learning_language="Japanese",
    support_language="English"
):

    word = (word or "").strip()
    reading = (reading or "").strip()
    romaji = (romaji or "").strip()
    meaning = (meaning or "").strip()
    part_of_speech = (part_of_speech or "").strip()
    role = (role or "").strip()
    learning_language = (
        learning_language or "Japanese"
    ).strip()
    support_language = (
        support_language or "English"
    ).strip()

    if not word:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO vocabulary (
            word,
            reading,
            romaji,
            meaning,
            part_of_speech,
            role,
            learning_language,
            support_language,
            reviewable
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)

        ON CONFLICT(
            word,
            learning_language,
            support_language
        )

        DO UPDATE SET

            reading =
                CASE
                    WHEN excluded.reading != ''
                    THEN excluded.reading
                    ELSE vocabulary.reading
                END,

            romaji =
                CASE
                    WHEN excluded.romaji != ''
                    THEN excluded.romaji
                    ELSE vocabulary.romaji
                END,

            meaning =
                CASE
                    WHEN excluded.meaning != ''
                    THEN excluded.meaning
                    ELSE vocabulary.meaning
                END,

            part_of_speech =
                CASE
                    WHEN excluded.part_of_speech != ''
                    THEN excluded.part_of_speech
                    ELSE vocabulary.part_of_speech
                END,

            role =
                CASE
                    WHEN excluded.role != ''
                    THEN excluded.role
                    ELSE vocabulary.role
                END,

            reviewable = 1
    """, (
        word,
        reading,
        romaji,
        meaning,
        part_of_speech,
        role,
        learning_language,
        support_language
    ))

    connection.commit()
    connection.close()

    return True


# =========================================================
# GET ALL VOCABULARY
# =========================================================

def get_all_vocabulary():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            word,
            reading,
            romaji,
            meaning,
            part_of_speech,
            role,
            learning_language,
            support_language,

            correct_count,
            wrong_count,
            review_count,
            mastery_score,
            last_reviewed,

            reviewable,

            created_at

        FROM vocabulary

        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()

    connection.close()

    return [dict(row) for row in rows]


# =========================================================
# RECORD REVIEW RESULT
# =========================================================

def record_review_result(
    vocabulary_id,
    correct
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            correct_count,
            wrong_count,
            review_count

        FROM vocabulary

        WHERE id = ?
    """, (vocabulary_id,))

    row = cursor.fetchone()

    if row is None:
        connection.close()
        return False

    correct_count = row["correct_count"] or 0
    wrong_count = row["wrong_count"] or 0
    review_count = row["review_count"] or 0

    review_count += 1

    if correct:
        correct_count += 1
    else:
        wrong_count += 1

    mastery_score = round(
        (correct_count / review_count) * 100,
        1
    )

    cursor.execute("""
        UPDATE vocabulary

        SET
            correct_count = ?,
            wrong_count = ?,
            review_count = ?,
            mastery_score = ?,
            last_reviewed = CURRENT_TIMESTAMP

        WHERE id = ?
    """, (
        correct_count,
        wrong_count,
        review_count,
        mastery_score,
        vocabulary_id
    ))

    connection.commit()
    connection.close()

    return True



# =========================================================
# GET WEAK VOCABULARY FOR SMART REVIEW
# =========================================================

def get_weak_vocabulary(limit=10):
    """
    Return vocabulary that needs practice.

    Priority:
    1. Words with low mastery scores.
    2. Words answered incorrectly more often.
    3. New words that have not been reviewed.

    Excludes:
    - Entries with empty words, readings, or meanings.
    - Entries containing Latin characters in the Japanese word.
    - Known invalid entries from earlier testing.
    - Words already mastered (80% or higher).
    """

    connection = get_connection()
    cursor = connection.cursor()

    # Prevent invalid entries created during earlier testing
    # from appearing in Smart Review.
    cursor.execute("""
        UPDATE vocabulary
        SET reviewable = 0
        WHERE
            (word = 'sh')
            OR (word = 'ハリ' AND LOWER(TRIM(meaning)) = 'hairs')
            OR (word = 'タルン' AND LOWER(TRIM(meaning)) = 'turn')
            OR (word = 'バブ' AND LOWER(TRIM(meaning)) = 'bubble')
    """)

    connection.commit()

    cursor.execute("""
        SELECT
            id,
            word,
            reading,
            romaji,
            meaning,
            part_of_speech,
            role,
            learning_language,
            support_language,
            correct_count,
            wrong_count,
            review_count,
            mastery_score,
            last_reviewed,
            reviewable,
            created_at

        FROM vocabulary

        WHERE
            reviewable = 1

            AND word IS NOT NULL
            AND TRIM(word) != ''

            AND reading IS NOT NULL
            AND TRIM(reading) != ''

            AND meaning IS NOT NULL
            AND TRIM(meaning) != ''

            -- Exclude words containing Latin letters.
            AND word NOT GLOB '*[A-Za-z]*'

            -- Exclude words that have already been mastered.
            AND (
                COALESCE(review_count, 0) = 0
                OR COALESCE(mastery_score, 0) < 80
            )

        ORDER BY
            CASE
                WHEN COALESCE(review_count, 0) = 0 THEN 1
                ELSE 0
            END ASC,

            COALESCE(mastery_score, 0) ASC,
            COALESCE(wrong_count, 0) DESC,
            COALESCE(last_reviewed, '') ASC

        LIMIT ?
    """, (max(1, min(int(limit), 100)),))

    rows = cursor.fetchall()
    connection.close()

    return [dict(row) for row in rows]


# =========================================================
# VOCABULARY STATISTICS
# =========================================================

def get_vocabulary_stats():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT

            COUNT(*) AS total_words,

            SUM(
                CASE
                    WHEN review_count > 0
                    THEN 1
                    ELSE 0
                END
            ) AS reviewed_words,

            SUM(
                CASE
                    WHEN mastery_score >= 80
                    THEN 1
                    ELSE 0
                END
            ) AS mastered_words,

            SUM(
                CASE
                    WHEN mastery_score < 50
                    THEN 1
                    ELSE 0
                END
            ) AS weak_words,

            COALESCE(
                SUM(correct_count),
                0
            ) AS total_correct,

            COALESCE(
                SUM(wrong_count),
                0
            ) AS total_wrong,

            COALESCE(
                SUM(review_count),
                0
            ) AS total_reviews

        FROM vocabulary

        WHERE reviewable = 1
    """)

    row = cursor.fetchone()

    connection.close()

    return dict(row)


# =========================================================
# REPAIR MISSING MEANINGS
# =========================================================

def repair_missing_meanings(
    meaning_map
):

    if not meaning_map:
        return

    connection = get_connection()
    cursor = connection.cursor()

    for word, meaning in meaning_map.items():

        if not meaning:
            continue

        cursor.execute("""
            UPDATE vocabulary

            SET meaning = ?

            WHERE
                word = ?
                AND (
                    meaning IS NULL
                    OR TRIM(meaning) = ''
                )
        """, (
            meaning.strip(),
            word.strip()
        ))

    connection.commit()
    connection.close()