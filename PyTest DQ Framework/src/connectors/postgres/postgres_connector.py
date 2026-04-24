
import psycopg2
import pandas as pd


class PostgresConnectorContextManager:
    def __init__(
            self,
            db_host: str,
            db_port: str,
            db_name: str,
            db_user: str,
            db_password: str
    ):
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.conn = None

    def __enter__(self):
        self.conn = psycopg2.connect(
            host=self.db_host,
            port=self.db_port,
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password
        )
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if self.conn:
            self.conn.close()

    def get_data_sql(self, sql):
        with self.conn.cursor() as cur:
            cur.execute(sql)
            header = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        return pd.DataFrame(rows, columns=header)
