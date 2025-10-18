DROP TABLE IF EXISTS public.credit_transactions CASCADE;

DELETE FROM public.organization_credit_transactions
WHERE transaction_type IN (
    'sql_query',
    'graphql_query',
    'chat_query',
    'text2sql',
    'agent_query'
);
