import sqlite3
from pathlib import Path


class Database:
    def __init__(self, db_path: str):
        """
        Initialize database connection.
        """
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self):
        """
        Create tables and indices if they do not exist.
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            path TEXT,
            fps REAL,
            width INTEGER,
            height INTEGER
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS frames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            frame_number INTEGER,
            timestamp REAL,
            FOREIGN KEY(video_id) REFERENCES videos(video_id)
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS landmarks (
            frame_id INTEGER,
            landmark_index INTEGER,
            x REAL,
            y REAL,
            z REAL,
            FOREIGN KEY(frame_id) REFERENCES frames(id)
        )
        """
        )

        # Indexes for performance
        cursor.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_frames_video
        ON frames(video_id)
        """
        )

        cursor.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_landmarks_frame
        ON landmarks(frame_id)
        """
        )

        self.conn.commit()

    def insert_video(self, video_id, path, fps, width, height):
        self.conn.execute(
            """
            INSERT OR IGNORE INTO videos (video_id, path, fps, width, height)
            VALUES (?, ?, ?, ?, ?)
            """,
            (video_id, path, fps, width, height),
        )
        self.conn.commit()

    def insert_frame(self, video_id, frame_number, timestamp):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO frames (video_id, frame_number, timestamp)
            VALUES (?, ?, ?)
            """,
            (video_id, frame_number, timestamp),
        )
        self.conn.commit()
        return cursor.lastrowid

    def insert_landmarks(self, frame_id, landmarks):
        """
        landmarks: iterable of (landmark_index, x, y, z)
        """
        self.conn.executemany(
            """
            INSERT INTO landmarks (frame_id, landmark_index, x, y, z)
            VALUES (?, ?, ?, ?, ?)
            """,
            [(frame_id, i, x, y, z) for i, x, y, z in landmarks],
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
