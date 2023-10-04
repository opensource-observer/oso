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


def execute_query(connection, query, col_names=False):
    try:
        cursor = connection.cursor()
        cursor.execute(query)
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
    finally:
        if cursor:
            cursor.close()


def close_connection(connection):
    if connection:
        connection.close()


def summarize_tables(db_connection):

    tables_to_query = [
        "event_pointer",
        "artifact",
        "event",
        "collection",
        "collection_projects_project",
        "project",
        "project_artifacts_artifact",
        "events_daily_by_artifact",
        "events_daily_by_project"
    ]
    for table in tables_to_query:
            # Query to get the number of rows
        count_query = f"SELECT COUNT(*) FROM {table};"
        count_result = execute_query(db_connection, count_query)
        
        # Query to get the column names
        column_query = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}';"
        column_result = execute_query(db_connection, column_query)

        # Get sample of the data
        sample_query = f"SELECT * FROM {table} LIMIT 5;"
        sample_result = execute_query(db_connection, sample_query)
        
        print(f"Table: {table}")
        if count_result:
            print(f"Row Count: {count_result[0][0]}")
        if column_result:
            print("Column Names:")
            for row in column_result:
                print("-", row[0])
        if sample_result:
            print("Sample Data:")
            for row in sample_result:
                print("-", row)
        print()


def dump_table(result, output_file):
    with open(output_file, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=",")
        for row in result:
            writer.writerow(row)


def save_query(db_connection, query_name):

    query_path = f"indexer/database/{query_name}.sql"
    with open(query_path) as sql_file:
        query = sql_file.read()
    result = execute_query(db_connection, query, col_names=True)
    
    output_file = f"indexer/_notebooks/tsdb/data/{query_name}.csv"
    dump_table(result, output_file)


def main():
    
    db_connection = connect_to_database()
    
    try:        
    
        query = """
        select 
            ep.collector, 
            count(*) as progress, 
            (
                select count(*)
                from project p
                left join
                    project_artifacts_artifact paa 
                    on paa."projectId" = p.id
                left join artifact a
                    on paa."artifactId" = a.id 
                where a."type" = 'GIT_REPOSITORY'
            ) as expected
        from event_pointer ep 
        where
            ep."startDate" < '2023-01-01'
        group by 
            ep.collector
        """
        result = execute_query(db_connection, query)
        print(result)

        #save_query(db_connection, "get_commits_by_project")
        #save_query(db_connection, "get_events_daily_by_project")
        
        #save_query(db_connection, "get_oss_contributions")
        #save_query(db_connection, "get_projects_by_collection")
        #summarize_tables(db_connection)

        #save_query(db_connection, "get_artifacts_by_project")
        #save_query(db_connection, "get_commits_by_collection")
        
        #save_query(db_connection, "get_project_event_stats")
        save_query(db_connection, "get_project_monthly_event_stats")
        #save_query(db_connection, "get_project_github_metrics")
    
        
    finally:
        close_connection(db_connection)


main()        