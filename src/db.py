import logging

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logger = logging.getLogger(__name__)


# noinspection SqlDialectInspection
class PagesDB:
    def __init__(self):
        self.conn = psycopg2.connect(dbname='postgres')
        self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        with self.conn.cursor() as curs:
            curs.execute(
                """
                CREATE TABLE IF NOT EXISTS pages (
                  id            SERIAL PRIMARY KEY,
                  url           TEXT NOT NULL UNIQUE,
                  date          TIMESTAMP WITH TIME ZONE,
                  last_modified TIMESTAMP WITH TIME ZONE,
                  text          TEXT      NOT NULL
                );   
                """
            )

            # Create md5 hash unique constraint for text.
            curs.execute(
                """
                CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS text_uni
                ON pages (CAST(md5(TEXT) AS UUID));
                """
            )

    def store(self, page):
        with self.conn.cursor() as curs:
            try:
                curs.execute(
                    """
                    INSERT INTO pages (url, date, last_modified, text) 
                    VALUES (%s, %s, %s, %s);
                    """,
                    [str(page.url.norm), page.date,
                     page.last_modified, page.text]
                )
                return True
            except:
                return False

    def size(self):
        with self.conn.cursor() as curs:
            curs.execute(
                """
                SELECT COUNT(*) FROM pages;
                """
            )
            return curs.fetchone()[0]

    def clear(self):
        with self.conn.cursor() as curs:
            curs.execute(
                """
                TRUNCATE TABLE pages;
                """,
            )
