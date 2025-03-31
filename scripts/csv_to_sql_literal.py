import argparse
import csv


def is_number(s):
    """Return True if s can be converted to a float."""
    try:
        float(s)
        return True
    except ValueError:
        return False

def sql_value(cell):
    """
    Convert a CSV cell to a SQL literal.
    Numbers are output as-is; text is quoted and any single quotes are escaped.
    """
    if is_number(cell):
        return cell
    else:
        cell = cell.replace("'", "''")
        return f"'{cell}'"

def csv_to_sql(csv_filename, sql_filename, table_alias="t"):
    with open(csv_filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        # Expect the first row to be the header with column names
        header = next(reader)
        rows = list(reader)
    
    with open(sql_filename, 'w', encoding='utf-8') as sqlfile:
        sqlfile.write("SELECT * FROM (\n  VALUES \n")
        row_lines = []
        for row in rows:
            values = [sql_value(cell) for cell in row]
            row_lines.append("    (" + ", ".join(values) + ")")
        sqlfile.write(",\n".join(row_lines))
        sqlfile.write("\n) AS " + table_alias + " (" + ", ".join(header) + ");\n")

def main():
    parser = argparse.ArgumentParser(
        description="Convert a CSV file into a SQL file using a VALUES clause."
    )
    parser.add_argument("csv_file", help="Path to the input CSV file.")
    parser.add_argument("sql_file", help="Path to the output SQL file.")
    parser.add_argument("--alias", default="t", help="Table alias to use (default: t).")
    args = parser.parse_args()
    
    csv_to_sql(args.csv_file, args.sql_file, args.alias)
    print(f"SQL file generated: {args.sql_file}")

if __name__ == '__main__':
    main()