import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

def run_query(query: str, params: tuple = None, fetch: bool = False):
    """
    Run a SQL query (CRUD support).
    """
    connection, cursor = None, None
    try:
        connection = psycopg2.connect(
            user=USER, password=PASSWORD, host=HOST, port=PORT, dbname=DBNAME
        )
        cursor = connection.cursor()
        cursor.execute(query, params)

        if fetch:
            rows = cursor.fetchall()
            connection.commit() 
            return rows
        else:
            connection.commit()
            return None
    except Exception as e:
        print(f"Error running query: {e}\nSQL: {query}\nParams: {params}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


    # # SELECT example
    # result = run_query("SELECT NOW();")
    # print("Current Time:", result)

    # # INSERT example
    # run_query("INSERT INTO test_table (name) VALUES (%s);", fetch=False, params=("Maryam",))
    # print("Row inserted!")
