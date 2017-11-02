import logging

import psycopg2

logger = logging.getLogger(__name__)


# noinspection SqlDialectInspection
class PagesDB:
    def __init__(self, name):
        self.name = name

        self.conn = psycopg2.connect(host='localhost', dbname='postgres')
        self.conn.set_isolation_level(0)

        with self.conn, self.conn.cursor() as curs:
            query = (
                """\
                CREATE TABLE IF NOT EXISTS {} (
                  id            SERIAL PRIMARY KEY,
                  url           TEXT NOT NULL UNIQUE,
                  date          TIMESTAMP WITH TIME ZONE,
                  last_modified TIMESTAMP WITH TIME ZONE,
                  title         TEXT      NOT NULL,
                  content       TEXT      NOT NULL
                );\
                """
            ).format(self.name)
            curs.execute(query)

            query = (
                "CREATE UNIQUE INDEX IF NOT EXISTS text_uni "
                "ON {} (CAST(md5(content) AS UUID));"
            ).format(self.name)
            curs.execute(query)

    def store(self, page, article):
        with self.conn, self.conn.cursor() as curs:
            try:
                query = (
                    "INSERT INTO {} (url, date, last_modified, title, content)"
                    " VALUES (%s, %s, %s, %s, %s);"
                ).format(self.name)
                args = [
                    str(page.url.norm), page.date, page.last_modified,
                    article.title, article.content
                ]
                curs.execute(query, args)
            except Exception:
                return False
            finally:
                return True

    def size(self):
        with self.conn, self.conn.cursor() as curs:
            query = (
                "SELECT COUNT(*) FROM {};"
            ).format(self.name)
            curs.execute(query)
            return curs.fetchone()[0]

    def drop(self):
        with self.conn, self.conn.cursor() as curs:
            query = (
                "DROP TABLE IF EXISTS {};"
            ).format(self.name)
            curs.execute(query)

    def close(self):
        self.conn.close()
