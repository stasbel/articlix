import logging

import psycopg2
import traceback

logger = logging.getLogger(__name__)


# noinspection SqlDialectInspection
class PagesDB:
    def __init__(self, name):
        self.name = name

        self.conn = psycopg2.connect(host='localhost',
                                     dbname='postgres',
                                     options='-c statement_timeout=1000', user='postgres')
        self.conn.set_isolation_level(0)

        with self.conn, self.conn.cursor() as curs:
            query = (
                """\
                CREATE TABLE IF NOT EXISTS {} (
                  id             SERIAL PRIMARY KEY,
                  url            TEXT NOT NULL UNIQUE,
                  date           TIMESTAMP WITH TIME ZONE,
                  last_modified  TIMESTAMP WITH TIME ZONE,
                  title          TEXT      NOT NULL,
                  content        TEXT      NOT NULL,
                  author         TEXT,
                  published_time TIMESTAMP WITH TIME ZONE,
                  publisher      TEXT,
                  estimate_time  INT,
                  likes          INT,
                  tags           TEXT,
                  comments       INT
                );\
                """
            ).format(self.name)
            curs.execute(query)

            query = (
                "CREATE UNIQUE INDEX IF NOT EXISTS text_uni "
                "ON {} (CAST(md5(content) AS UUID));"
            ).format(self.name)
            curs.execute(query)

    def store(self, article):
        with self.conn, self.conn.cursor() as curs:
            try:
                query = (
                    """\
                    INSERT INTO {}
                    (url, date, last_modified, 
                    title, content,
                    author, published_time, publisher, 
                    estimate_time,
                    likes, tags, comments)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);\
                    """
                ).format(self.name)
                page = article.page
                args = [
                    str(page.url.norm), page.date, page.last_modified,
                    article.title, article.content,
                    article.author, article.published_time, article.publisher,
                    article.estimate_time,
                    article.likes, article.tags, article.comments
                ]
                curs.execute(query, args)
            except Exception:
                logger.warning('Store db error at `%s`', page.url)
                return False
            finally:
                return True

    def size(self):
        size = None
        while size is None:
            try:
                with self.conn, self.conn.cursor() as curs:
                    query = (
                        "SELECT COUNT(*) FROM {};"
                    ).format(self.name)
                    curs.execute(query)
                    size = curs.fetchone()[0]
            except:
                logger.error('Size db error')
        return size

    def drop(self):
        with self.conn, self.conn.cursor() as curs:
            query = (
                "DROP TABLE IF EXISTS {};"
            ).format(self.name)
            curs.execute(query)

    def close(self):
        self.conn.close()
