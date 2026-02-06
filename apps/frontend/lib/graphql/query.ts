import { logger } from "@/lib/logger";
import { TypedDocumentNode } from "@graphql-typed-document-node/core";
import { print } from "graphql";

export async function executeGraphQL<TResult, TVariables>(
  document: TypedDocumentNode<TResult, TVariables>,
  variables: TVariables,
  errorMessage: string,
): Promise<TResult> {
  const query = print(document);
  const response = await fetch("/api/v1/osograph", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query,
      variables,
    }),
  });

  const result = await response.json();

  if (result.errors) {
    logger.error(`${errorMessage}:`, result.errors[0].message);
    throw new Error(`${errorMessage}: ${result.errors[0].message}`);
  }

  if (!result.data) {
    throw new Error(`No response data from mutation`);
  }

  return result.data as TResult;
}
