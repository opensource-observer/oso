import { google } from "@ai-sdk/google";
import { streamText } from "ai";
import { experimental_createMCPClient as createMCPClient } from "ai";
import { supabasePrivileged } from "../../../../lib/clients/supabase";
import { logger } from "../../../../lib/logger";

export const maxDuration = 60;

export async function POST(req: Request) {
  const { messages } = await req.json();

  const authHeader = req.headers.get("authorization");

  if (!authHeader) {
    return new Response(JSON.stringify({ error: "Authentication required" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  const token = authHeader.startsWith("Bearer ")
    ? authHeader.substring(7)
    : authHeader;

  try {
    const { data: userData, error: userError } =
      await supabasePrivileged.auth.getUser(token);

    if (userError || !userData.user) {
      return new Response(JSON.stringify({ error: "Invalid authentication" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    }

    const userId = userData.user.id;

    const { data: apiKeyData, error: apiKeyError } = await supabasePrivileged
      .from("api_keys")
      .select("api_key")
      .eq("user_id", userId)
      .is("deleted_at", null)
      .order("created_at", { ascending: false })
      .limit(1)
      .single();

    if (apiKeyError || !apiKeyData) {
      return new Response(
        JSON.stringify({ error: "No API key found for user" }),
        {
          status: 403,
          headers: { "Content-Type": "application/json" },
        },
      );
    }

    const userApiKey = apiKeyData.api_key;

    const mcpClient = await createMCPClient({
      transport: {
        type: "sse",
        url: process.env.OSO_MCP_SERVER_URL!,
        headers: {
          Authorization: `Bearer ${userApiKey}`,
        },
      },
    });

    const result = streamText({
      model: google("gemini-2.5-pro-exp-03-25"),
      system: `You are a helpful SQL assistant for the OSO (OpenSource Observer) data lake.
Your purpose is to help users explore and analyze open source project data.
Always provide accurate and helpful responses about the OSO data.
When providing SQL queries, make sure they are valid for the OSO schema.
Use the query_oso, list_tables, and get_table_schema tools to provide accurate answers.
Format your SQL queries with proper indentation and keywords in uppercase.
When showing results, provide a brief explanation of what the data means. All the snippets
must be valid SQL queries in the Pesto dialect. Do not use any other dialects or SQL engines.`,
      messages,
      tools: await mcpClient.tools(),
      maxSteps: 50,
      onFinish: async () => {
        await mcpClient.close();
      },
      onError: async (error) => {
        logger.error("Error in chat route:", error);
      },
      maxTokens: 2000,
    });

    return result.toDataStreamResponse({
      sendUsage: true,
      sendReasoning: true,
    });
  } catch (error) {
    logger.error("Error in chat route:", error);
    return new Response(
      JSON.stringify({ error: "An error occurred processing your request" }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      },
    );
  }
}
