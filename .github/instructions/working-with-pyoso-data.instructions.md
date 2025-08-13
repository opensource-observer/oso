#### 0. One-time setup

Always start by defined the pyoso client with the OSO_API_KEY

```python
from pyoso import Client
import os
client = Client(os.getenv("OSO_API_KEY"))   # never hard-code keys
```

---

#### 1. Generate SQL

Call the `query_text2sql_agent()` MCP tool and pass in the user's natural language query and it will return a SQL query.

Don't ever call the MCP tool in python code, just use it yourself to gather the proper SQL query. Only the end result SQl query should be written into the code.

```python
sql_query = 'output of query_text2sql_agent MCP tool'
```

---

#### 2. Run the SQL query across the DB

Pass in the sql_query gathered above into thepyoso client defined above with .to_pandas(), which should return a dataframe result of the query across pyoso's data lake.

```python
df = client.to_pandas(sql_query)
```

---

#### 3. (Optional) Analysis

Now, based on the user's request, you are free to continue working with the final dataframe and run any additional analysis they might want done on it.

---
