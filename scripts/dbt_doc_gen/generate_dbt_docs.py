# !pip install openai
# !pip install pandas-gbq
# pip install pymongo

from typing import List, Dict, Any, Union, Tuple, Callable, Optional
from pandas_gbq import gbq
import openai
from google.colab import auth
import numpy as np
import json
import yaml
from pymongo import MongoClient

auth.authenticate_user()

# password to mongodb database
db_password = "" # insert mongo password
# url to connect to mongodb database
mongo_uri = "" # insert mongo url
# openai api key
OPENAIAPIKEY = '' # insert key here

# connect to the mongodb database
client = MongoClient(mongo_uri)
db = client["data_dictionary"]

collections = db.list_collection_names()
collection = db["data_dict"]

# dictionary of datasets and projects to scrape
projects = {
    'oso-data-436717' : ['arbitrum_one','farcaster','filecoin','gitcoin','lens','open_collective','openrank','oso_playground','oso_production','oso_projects','superchain'],
    'githubarchive' : ['day', 'github', 'month', 'year'],
    'bigquery-public-data' : [
      "crypto_ethereum",
      "crypto_ethereum_classic",
      "crypto_iotex",
      "crypto_kusama",
      "crypto_litecoin",
      "crypto_multiversx_mainnet_eu",
      "crypto_near_mainnet_us",
      "crypto_polkadot",
      "crypto_polygon",
      "crypto_solana_mainnet_us",
      "crypto_sui_mainnet_us",
      "crypto_tezos",
      "crypto_theta",
      "crypto_zcash",
      "crypto_zilliqa",
      'blockchain_analytics_ethereum_mainnet_us',
      'crypto_aptos_mainnet_us',
      'crypto_aptos_testnet_us',
      'crypto_band',
      'crypto_bitcoin',
      'crypto_bitcoin_cash',
      'crypto_cardano',
      'crypto_cosmos_mainnet_us',
      'crypto_cosmos_testnet_us',
      'crypto_dash',
      'crypto_dogecoin',
      'ethereum_blockchain',
      "goog_blockchain_arbitrum_one_us",
      "goog_blockchain_avalanche_contract_chain_us",
      "goog_blockchain_cronos_mainnet_us",
      "goog_blockchain_ethereum_goerli_us",
      "goog_blockchain_ethereum_mainnet_us",
      "goog_blockchain_fantom_opera_us",
      "goog_blockchain_optimism_mainnet_us",
      "goog_blockchain_polygon_mainnet_us",
      "goog_blockchain_tron_mainnet_us"
    ]
}

# prompt passed into the LLM for column description generation
column_description_prompt = """
You will receive a JSON object containing metadata about a dataset column. This object includes:
- `dataset_context`: A brief explanation of the dataset’s domain and purpose.
- `table_name`: The name of the table that holds the column.
- `column_name`: The name of the column to describe.
- `data_type`: The type of data stored in the column (e.g., integer, string, timestamp).
- `sample_values`: A few example values from the column.
- `random_values`: Randomly generated values illustrating the range of possible values in the column.
- `mode`: The column’s most frequent or common value.

Your task:
- Write a short and concise description of the column that explains its role and significance in the context of the dataset.
- Keep the description limited to **2-3 sentences**.
- Avoid technical jargon unless it's necessary to understand the column's purpose.
- Make sure the description is understandable for someone familiar with the dataset’s domain but avoid overly technical or redundant information.

Output the result in the following JSON format:
{
  "column_name": "A clear and concise description of what the column represents and how it might be used, specific to the dataset’s domain."
}

Focus on clarity, simplicity, and relevance to the dataset’s domain and purpose.
"""

# prompt passed into the LLM for table description generation
table_description_prompt = """
You will receive a JSON object containing metadata about a dataset column. This object includes:
- `dataset_context`: A brief explanation of the dataset’s domain and purpose.
- `table_name`: The name of the table.
- `columns`: The list of the columns of the dataset.
  - `column_name`: The name of the column.
  - `data_type`: The type of data stored in the column (e.g., integer, string, timestamp).
  - `sample_values`: A few example values from the column.
  - `random_values`: Randomly generated values illustrating the range of possible values in the column.
  - `mode`: The column’s most frequent or common value.

Your task:
- Write a short and concise description of the table that explains its role and significance in the context of the dataset.
- Keep the description limited to **2-3 sentences**.
- Avoid technical jargon unless it's necessary to understand the column's purpose.
- Make sure the description is understandable for someone familiar with the dataset’s domain but avoid overly technical or redundant information.

Output the result in the following JSON format:
{
  "table_name": "A clear and concise description of what the table represents and how it might be used, specific to the dataset’s domain."
}

Focus on clarity, simplicity, and relevance to the dataset’s domain and purpose.
"""

# load the data that already exists in the mongodb database
def load_existing_data(collection) -> List[Dict[str, Any]]:
    existing_data = list(collection.find())
    return existing_data

# recursively patch the datatypes of the data before storing it into the mongodb database
def convert_np_types(document: Union[Dict, List, np.integer, np.floating, np.ndarray, Any]) -> Union[Dict, List, int, float, Any]:
    if isinstance(document, dict):
        return {k: convert_np_types(v) for k, v in document.items()}
    elif isinstance(document, list):
        return [convert_np_types(v) for v in document]
    elif isinstance(document, np.integer):
        return int(document)
    elif isinstance(document, np.floating):
        return float(document)
    elif isinstance(document, np.ndarray):
        return document.tolist()
    else:
        return document

# append the cleaned data into the mongodb database
def store_data(table_info: Dict[str, Any], collection) -> None:
    cleaned_data = convert_np_types(table_info)
    collection.insert_one(cleaned_data)
    return

# iterate through the provided datasets, and create a list of tables within each dataset
def extract_table_names(datasets: List[str], project_name: str) -> Dict[str, List[str]]:
    table_names = {}

    for dataset in datasets:
        # query to get a list of tables from each dataset
        table_info_address = f"`{project_name}.{dataset}.INFORMATION_SCHEMA.TABLES`"

        query = f"""
        SELECT *
        FROM {table_info_address}
        """

        result = gbq.read_gbq(query, project_id=project_name)
        # store tables in the dictionary with dataset as the key and tables as a list
        table_names[dataset] = list(result['table_name'].values)

    return table_names

# iterate through each table and extract and create a list of columns within each table
def extract_columns(table_names: Dict[str, List[str]], project_name: str) -> Dict[str, Dict[str, List[Tuple[str, str, str]]]]:
    cols = {}

    for dataset, tables in table_names.items():
        # query to get a list of columns with each table
        cols[dataset] = {}
        table_info_address = f"`{project_name}.{dataset}.INFORMATION_SCHEMA.COLUMNS`"

        query = f"""
        SELECT *
        FROM {table_info_address}
        """
        result = gbq.read_gbq(query, project_id=project_name)

        # iterate through each row (which represents a column within a table) and store it
        for idx, row in result.iterrows():
            table = row['table_name']

            if table not in cols[dataset]:
                cols[dataset][table] = []

            # keep track of each columns data type and if it's nullable
            row_info = (row['column_name'], row['is_nullable'], row['data_type'])
            cols[dataset][table].append(row_info)

    return cols

# for each column, extract and store the first 10 rows and then a random 10 rows
def extract_rows_from_cols(cols: Dict[str, Dict[str, List[Tuple[str, str, str]]]], project_name: str) -> Dict[str, Dict[str, List[Tuple[Tuple[str, str, str], List[Any], List[Any]]]]]:
    rows = {}

    for dataset in cols:
        rows[dataset] = {}

        for table in cols[dataset]:
            rows[dataset][table] = []

            for col in cols[dataset][table]:
                # if the datatype is JSON, we have to convert the JSON data into a string so it can be read in
                if col[2] == 'JSON':
                    first_ten_query = f'''
                    SELECT TO_JSON_STRING(`{col[0]}`) as {col[0]}
                    FROM `{project_name}.{dataset}.{table}`
                    LIMIT 10
                    '''
                    rand_ten_query = f'''
                    SELECT TO_JSON_STRING(`{col[0]}`) as {col[0]}
                    FROM `{project_name}.{dataset}.{table}`
                    ORDER BY RAND()
                    LIMIT 10
                    '''

                # otherwise we can query like normal
                else:
                    first_ten_query = f'''
                    SELECT `{col[0]}`
                    FROM `{project_name}.{dataset}.{table}`
                    LIMIT 10
                    '''
                    rand_ten_query = f'''
                    SELECT `{col[0]}`
                    FROM `{project_name}.{dataset}.{table}`
                    ORDER BY RAND()
                    LIMIT 10
                    '''

                # store the rows into the dictionary
                first_ten = list(gbq.read_gbq(first_ten_query, project_id=project_name)[col[0]].values)
                rand_ten = list(gbq.read_gbq(rand_ten_query, project_id=project_name)[col[0]].values)

                rows[dataset][table].append((col, first_ten, rand_ten))

    return rows

# function to extract all of the relevant info for provided datasets
def extract_table_info(datasets: List[str], project_name: str) -> Dict[str, List[Dict[str, Any]]]:
    table_names = extract_table_names(datasets, project_name)
    cols = extract_columns(table_names, project_name)
    rows = extract_rows_from_cols(cols, project_name)

    data_dict = {}

    for dataset in table_names:
        data_dict[dataset] = []
        for table in table_names[dataset]:
            table_dict = {'table_name': table, 'columns': []}

            # build the new dictionary based on the extracted information above
            for col in cols[dataset][table]:
                col_dict = {
                    'column_name': col[0],
                    'data_type': col[2],
                    'sample_values': rows[dataset][table][0][1],
                    'random_values': rows[dataset][table][0][2],
                    'mode': 'nullable' if col[1] == 'YES' else 'not_nullable'
                }
                table_dict['columns'].append(col_dict)

            data_dict[dataset].append(table_dict)

    return data_dict

# clean the outputs of the LLM
def clean_column_descriptions(description: str) -> Dict[str, Any]:
  print(description)
  cleaned_description = description.replace('```json', '').replace('```', '').replace('\n', '')
  print(cleaned_description)
  description_json = json.loads(cleaned_description)
  return description_json

# prompt the LLM with the passed prompt and context
def generate_prompt(context: str, prompt: str) -> Dict[str, Any]:
    openai.api_key = OPENAIAPIKEY

    updated_prompt = prompt + context
    completion = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": updated_prompt}
        ]
    )

    description = completion.choices[0].message.content
    return clean_column_descriptions(description)

# generate the description for a single table
def generate_context_single(dataset_name: str, dataset: Dict[str, Any]) -> Dict[str, Any]:
    table_name = dataset['table_name']
    columns = dataset['columns']

    dataset_context_path = f'dataset_context/{dataset_name}.json'

    with open(dataset_context_path, 'r') as f:
        dataset_context = json.load(f)

    for column in columns:
        column_context = {
            'dataset_context': dataset_context,
            'table_name': table_name,
            'column_name': column['column_name'],
            'data_type': column['data_type'],
            'sample_values': column['sample_values'],
            'random_values': column['random_values'],
            'mode': column['mode']
        }

        column_description_dict = generate_prompt(str(column_context), column_description_prompt)
        column['description'] = list(column_description_dict.values())[0]

    return dataset

# generate the description for the entire collection
def generate_context(collection: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for dataset in collection[0].keys():
        table_name = collection[0][dataset]['table_name']
        columns = collection[0][dataset]['columns']

        dataset_context_path = f'dataset_context/{dataset}.json'

        with open(dataset_context_path, 'r') as f:
            dataset_context = json.load(f)

        for column in columns:
            column_context = {
                'dataset_context': dataset_context,
                'table_name': table_name,
                'column_name': column['column_name'],
                'data_type': column['data_type'],
                'sample_values': column['sample_values'],
                'random_values': column['random_values'],
                'mode': column['mode']
            }

            column_description_dict = generate_prompt(str(column_context), column_description_prompt)
            column['description'] = list(column_description_dict.values())[0]

    return collection

# clear the mongodb database
def clear(collection) -> None:
    collection.delete_many({})

# update the table in the database with the new descriptions
def add_new_table(database: Dict[str, Any], dataset: str, table: Dict[str, Any], table_name: str, keys: set, dataset_present: bool) -> Tuple[Dict[str, Any], set]:
    table = generate_context_single(dataset, table)
    table = generate_table_description(table, dataset)
    if dataset_present:
        database[dataset].append(table)
    else:
        database[dataset] = [table]
    keys.add(table_name)

    return database, keys

# helper function to return a dataset if it exists and return null otherwise
def find_dataset(database: Union[List[Dict[str, Any]], Dict[str, Any]], dataset: str, table = None) -> Union[Dict[str, Any], None]:
    if isinstance(database, list):
        for ds in database[::-1]:
            if dataset in ds.keys():
                if table:
                    for t in ds[dataset]:
                        if t['table_name'] == table:
                            return t
                return ds[dataset]
    elif isinstance(database, dict):
        if dataset in database.keys():
            if table:
                for t in database[dataset]:
                    if t['table_name'] == table:
                        return t
            return database[dataset]

    return None

# check to see if the passed set of columns is equal to the columns of the existing dataset
def check_existing_columns(existing_data, dataset: str, table: str, columns: set) -> bool:
    existing_table = find_dataset(existing_data, dataset, table)
    if existing_table:
        existing_columns = set([(column["column_name"], column['data_type']) for column in existing_table["columns"]])
        return (columns == existing_columns)
    return False

def generate_table_description(table_info, dataset_name):

  dataset_context_path = f'/content/drive/MyDrive/OSO/dataset_context/{dataset_name}.json'

  with open(dataset_context_path, 'r') as f:
    dataset_context = json.load(f)
  
  dataset_context = "Important context description for the dataset: " + dataset_context
  table_description_dict = generate_prompt(str(table_info), table_description_prompt + dataset_context)
  table_info['description'] = list(table_description_dict.values())[0]

  return table_info

def json_to_yml(working_data, yml_path = None):
  yml = {}

  for dataset, tables in working_data.items():
    yml[dataset] = []
    for table in tables:
      table_info = {
          'name': table['table_name'],
          'meta': {'contributors':'oso_team'},
          'description': table['description'],
          'columns': [{'name': col['column_name'], 'description':col['description']} for col in table['columns']]
      }
      yml[dataset].append(table_info)

  if yml_path:
    with open(yml_path, 'w') as f:
      yaml.dump(yml, f)

  return yml

def filter_datasets(dataset):
  table_name = dataset.split('.')[-1]
  if table_name[:4] == 'stg_' or table_name[-2:] == 'v0' or table_name[-2:] == 'v1':
    return True
  return False

def main(projects: Dict[str, List[str]], clear_contents: bool = False, comparator: Optional[Callable[[str], bool]] = None, save_file_path = None, yml_file_path = None) -> Dict[str, Any]:
    # clear mongodb database (we don't actually clear the database until the end of the function in case there are errors)
    if clear_contents:
        working_data = {}
    # retrieve existing data and remove the id of the mongodb database
    else:
        existing_data = load_existing_data(collection)[-1]
        if 'rag' in existing_data.keys():
          working_data = existing_data['rag'].copy()
        else:
          working_data = existing_data.copy()
        if '_id' in working_data.keys():
          del working_data['_id']

    # generate a set of all of the tables of each dataset
    keys = []
    for dataset in working_data.keys():
        if dataset != '_id':
            for table in dataset:
                keys.append(f"{dataset}.{table}")
    keys = set(keys)

    # iterate through each of the provided projects
    for project_name, datasets in projects.items():
        print(f"Project: {project_name}")

        # extract all of the relevant info on the project (tables, columns + datatypes)
        table_info = extract_table_info(datasets, project_name)

        # iterate through each table
        for dataset in table_info.keys():
            # check if the dataset already exists
            dataset_present = False if not find_dataset(working_data, dataset) else True

            for table in table_info[dataset]:
              table_name = f"{dataset}.{table['table_name']}"
              print(f"Working on table: {table_name}")
              # apply filter if applicable
              if comparator and not comparator(table_name):
                print('Comparator failed.')
                continue

              # if the table doesn't exist generate descriptions and add it to the database
              if table_name not in keys:
                  working_data, keys = add_new_table(working_data, dataset, table, table_name, keys, dataset_present)
              # if the table already exists, determine whether to update the descriptions based on whether or not the columns have been updated
              else:
                  column_details = table["columns"]
                  columns = set([(column["column_name"], column['data_type']) for column in column_details])

                  # if the columns are different, generate descriptions and add it to the database
                  if not check_existing_columns(working_data, dataset, table['table_name'], columns):
                      working_data, keys = add_new_table(working_data, dataset, table, table_name, keys, dataset_present)

    # now clear the contents already in the mongodb database
    if clear_contents:
        clear(collection)
    # convert the json data into the desired yml format
    output = {'rag': working_data, 'yml': json_to_yml(working_data, yml_file_path)}
    # store the updated data into the mongodb database
    store_data(output, collection)

    # save json file to desired file path
    if save_file_path:
        with open(save_file_path, 'w') as f:
            json.dump(working_data, f)

    return output

if __name__ == "__main__":
    main(projects, clear_contents=True, comparator=filter_datasets, yml_file_path='projects.yml')