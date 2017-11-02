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
            curs.execute(
                """
                CREATE TABLE IF NOT EXISTS {} (
                  id            SERIAL PRIMARY KEY,
                  url           TEXT NOT NULL UNIQUE,
                  date          TIMESTAMP WITH TIME ZONE,
                  last_modified TIMESTAMP WITH TIME ZONE,
                  text          TEXT      NOT NULL
                );   
                """.format(self.name)
            )

            curs.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS text_uni
                ON {} (CAST(md5(TEXT) AS UUID));
                """.format(self.name)
            )

    def store(self, page):
        try:
            with self.conn, self.conn.cursor() as curs:
                curs.execute(
                    """
                    INSERT INTO {} (url, date, last_modified, text) 
                    VALUES (%s, %s, %s, %s);
                    """.format(self.name),
                    [
                        str(page.url.norm),
                        page.date,
                        page.last_modified,
                        page.text
                    ]
                )
            return True
        except:
            return False

    def size(self):
        with self.conn, self.conn.cursor() as curs:
            curs.execute(
                """
                SELECT COUNT(*) FROM {};
                """.format(self.name)
            )
            return curs.fetchone()[0]

    def drop(self):
        with self.conn, self.conn.cursor() as curs:
            curs.execute(
                """
                DROP TABLE IF EXISTS {};
                """.format(self.name)
            )

    def close(self):
        self.conn.close()
