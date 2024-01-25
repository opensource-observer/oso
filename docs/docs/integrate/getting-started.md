---
sidebar_position: 1
---

# Getting started

:::warning
This page is a work in progress.
:::

This guide will quickly take you through how to quickly get started with the OSO API.

## Create an account

First, navigate to [www.opensource.observer](https://www.opensource.observer) and create a new account.
If you already have an account, log in.

## Create a new personal API key

1. Go to [Account settings](https://www.opensource.observer/app/settings)
2. In the "Personal API Keys" section, click "+ Create a Personal API Key"
3. Give your key a label - this is just for you, usually to describe a key's purpose.
4. At the top of your list, you should see your brand new key. **Immediately** copy its value, as you'll **never** see it again after refreshing the page.

You can create as many keys as you like

## Make GraphQL queries

All API requests are sent to the following URL:

```
Coming soon...
```

In order to authenticate with the API service, you have to use the `Authorization` HTTP header and `Bearer` authentication on all HTTP requests, like so:

```js
const headers = {
  Authorization: `Bearer ${PERSONAL_API_KEY}`
};
``

### Rate limiting

All requests are rate limited. There are separate rate limits for different resources:

### GraphQL Explorer

```
