import csv
import os
import psycopg2
from dotenv import load_dotenv


def connect_to_database():
    load_dotenv()
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    connection_string = f"postgres://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    try:
        connection = psycopg2.connect(connection_string)
        return connection
    except psycopg2.Error as e:
        print("Error connecting to the database:", e)
        return None


def execute_query(connection, query, params=None, col_names=False):
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            if col_names:
                results = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                results = [column_names] + results
            else:
                results = cursor.fetchall()
            return results
    except psycopg2.Error as e:
        print("Error executing query:", e)
        return None


def close_connection(connection):
    if connection:
        connection.close()


def read_query_from_file(filename):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    with open(path, 'r') as file:
        query = file.read()
    return query


def dump_results_to_csv(results, filename):
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../_notebooks/tsdb/{filename}.csv")
    with open(local_path, 'w') as file:
        writer = csv.writer(file)
        writer.writerows(results)


def query_events_and_dump_to_csv(query_file, collection_slug, postfix, start_date='2016-01-01'):
    db_connection = connect_to_database()
    
    try:
        query = read_query_from_file(query_file)
        params = (start_date, collection_slug)
        result = execute_query(db_connection, query, params=params, col_names=True)

        if result:
            filename = f"{collection_slug}_{postfix}"
            dump_results_to_csv(result, filename)
    
    finally:
        close_connection(db_connection)

def sandbox():

    db_connection = connect_to_database()
    query = """
    SELECT * FROM projects
    """
    result = execute_query(db_connection, query)
    print(result)


def main():
    # query_events_and_dump_to_csv(
    #     "get_monthly_commits_by_collection_after_first_star.sql", 
    #     #"optimism",
    #     "gitcoin-allo",
    #     "filtered_commits"
    # )
    query_events_and_dump_to_csv(
        "get_filtered_monthly_contributors_by_collection.sql", 
        "optimism",
        "filtered_contributors"
    )

if __name__ == "__main__":
    main()
    #sandbox()
