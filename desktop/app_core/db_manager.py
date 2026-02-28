"""
Database Manager Module

PostgreSQL-only. SQLite support has been permanently removed.
All database access goes through PostgresManager (psycopg2).
"""

import os
from pathlib import Path

import streamlit as st


@st.cache_resource(show_spinner=False)
def get_db_manager(test_mode: bool = False):
    """
    Returns the PostgresManager instance.

    The test_mode parameter is retained for call-site compatibility but is ignored.
    All environments (dev, test, prod) must use a PostgreSQL DATABASE_URL.
    """
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url or not db_url.startswith("postgresql"):
        raise RuntimeError(
            "SADDL requires a PostgreSQL connection. "
            "Set the DATABASE_URL environment variable to a postgresql:// URL. "
            f"Current value: {repr(db_url) if db_url else '(not set)'}"
        )
    from app_core.postgres_manager import PostgresManager
    return PostgresManager(db_url)
