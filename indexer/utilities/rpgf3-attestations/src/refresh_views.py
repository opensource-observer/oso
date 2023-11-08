from dotenv import load_dotenv
import os
import psycopg2


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


def refresh_mv(sql):
    conn = connect_to_database()
    conn.autocommit = True
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
    except Exception as e:
        print(e)
    finally:
       cursor.close()


def main():

    start_date = '2013-01-01'
    end_date = '2023-11-06'
    mvs = [
        'events_daily_to_artifact',
        'events_daily_to_project',
    
        'events_weekly_to_artifact',
        'events_weekly_to_project',

        'events_monthly_to_artifact',
        'events_monthly_to_project',

        'events_daily_from_artifact',
        'events_daily_from_project',

        'events_weekly_from_artifact',
        'events_weekly_from_project',

        'events_monthly_from_artifact'
        'events_monthly_from_project'
    ]
    for mv in mvs:
        
        sql = f"CALL refresh_continuous_aggregate('{mv}', '{start_date}', '{end_date}');"
        print("Executing...", mv)
        start_time = time.time()
        refresh_mv(sql)
        end_time = time.time()
        print(f"Query took: {round(end_time-start_time)} seconds")       

    print("Executing...")
    sql = "REFRESH MATERIALIZED VIEW first_contribution;"
    refresh_mv(sql)


if __name__ == "__main__":
    main()    