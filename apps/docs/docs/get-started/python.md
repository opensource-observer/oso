---
title: "Access via Python"
sidebar_position: 1
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

The [OSO](https://www.opensource.observer) API serves
queries on metrics and metadata about open source projects.
It is a [GraphQL](https://graphql.org/) API backed by the
[OSO data pipeline](../references/architecture.md).

Let's make your first query in under five minutes.

## Generate an API key

First, go to [www.opensource.observer](https://www.opensource.observer) and create a new account.

If you already have an account, log in. Then create a new personal API key:

1. Go to [Account settings](https://www.opensource.observer/app/settings)
2. In the "API Keys" section, click "+ New"
3. Give your key a label - this is just for you, usually to describe a key's purpose.
4. You should see your brand new key. **Immediately** save this value, as you'll **never** see it again after refreshing the page.
5. Click "Create" to save the key.

![generate API key](../integrate/generate-api-key.png)

## Prepare your query

You can navigate to our
[public GraphQL explorer](https://www.opensource.observer/graphql)
to explore the schema and execute test queries.

![GraphQL explorer](../integrate/api-explorer.gif)

For example, this query will fetch the first 10 projects in
[oss-directory](https://github.com/opensource-observer/oss-directory).

```graphql
query GetProjects {
  oso_projectsV1(limit: 10) {
    description
    displayName
    projectId
    projectName
    projectNamespace
    projectSource
  }
}
```

## Issue your first API request

All API requests are sent to the following URL:

```
https://www.opensource.observer/api/v1/graphql
```

In order to authenticate with the API service, you have to use the `Authorization` HTTP header and `Bearer` authentication on all HTTP requests

<Tabs>
  <TabItem value="curl" label="curl" default>
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DEVELOPER_API_KEY" \
  -d '{"query":"query GetProjects { oso_projectsV1(limit: 10) { description displayName projectId projectName projectNamespace projectSource } }"}' \
  https://www.opensource.observer/api/v1/graphql
```
  </TabItem>
  <TabItem value="javascript" label="JavaScript">
 ```js
 const query = `
   query GetProjects {
     oso_projectsV1(limit: 10) {
       description
       displayName
       projectId
       projectName
       projectNamespace
       projectSource
     }
   }
 `;
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${DEVELOPER_API_KEY}`,
};
 
const response = await fetch('https://www.opensource.observer/api/v1/graphql', {
  method: 'POST',
  headers: headers,
  body: JSON.stringify({
    query: query
  }),
});

const data = await response.json();
console.log(data);

````
  </TabItem>
  <TabItem value="python" label="Python">
```python
import requests

query = """
query GetProjects {
  oso_projectsV1(limit: 10) {
    description
    displayName
    projectId
    projectName
    projectNamespace
    projectSource
  }
}
"""

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {DEVELOPER_API_KEY}'
}

response = requests.post(
    'https://www.opensource.observer/api/v1/graphql',
    json={'query': query},
    headers=headers
)

data = response.json()
print(data)
````

  </TabItem>
</Tabs>

## Next steps

Congratulations! You've made your first API request.
Now try one of our tutorials.

- [Analyze a collection of projects](../tutorials/collection-view)
- [Deep dive into a project](../tutorials/project-deepdive)
