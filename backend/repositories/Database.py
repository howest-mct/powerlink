import mysql.connector
import os
from contextlib import contextmanager
import logging


class Database:

    @staticmethod
    @contextmanager
    def __open_connection(
        config_path: str = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../config.ini")
        )
    ):
        try:
            db = mysql.connector.connect(
                option_files=config_path,
                autocommit=False,
            )
            if not db.is_connected():
                raise Exception("Failed to connect to the database")
            cursor = db.cursor(dictionary=True, buffered=True)
            yield db, cursor
            db.commit()
        except mysql.connector.Error as err:
            db.rollback()
            if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
                logging.error("Error: Access denied to the database")
            elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                logging.error("Error: Database not found")
            else:
                logging.error(f"Database error: {err}")
            raise
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def get_rows(sql_query: str, params=None):
        with Database.__open_connection() as (db, cursor):
            try:
                cursor.execute(sql_query, params)
                result = cursor.fetchall()
                return result if result else []
            except mysql.connector.Error as error:
                logging.error(f"Query failed: {error}")
                return None

    @staticmethod
    def get_one_row(sql_query: str, params=None):
        with Database.__open_connection() as (db, cursor):
            try:
                cursor.execute(sql_query, params)
                result = cursor.fetchone()
                if result is None:
                    raise ValueError("No record found")
                return result
            except mysql.connector.Error as error:
                logging.error(f"Query failed: {error}")
                return None

    @staticmethod
    def execute_sql(sql_query: str, params=None):
        with Database.__open_connection() as (db, cursor):
            try:
                cursor.execute(sql_query, params)
                if cursor.lastrowid != 0:
                    return cursor.lastrowid
                else:
                    if cursor.rowcount == -1:
                        raise Exception("SQL error occurred")
                    return cursor.rowcount
            except mysql.connector.Error as error:
                db.rollback()
                logging.error(f"Error: Data not saved. {error}")
                return None
