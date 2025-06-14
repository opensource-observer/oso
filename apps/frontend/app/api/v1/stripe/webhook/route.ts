import { type NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import Stripe from "stripe";
import { getStripeClient, extractIntentString } from "@/lib/clients/stripe";
import { createPrivilegedSupabaseClient } from "@/lib/clients/supabase";
import { logger } from "@/lib/logger";
import { STRIPE_WEBHOOK_SECRET } from "@/lib/config";

const stripe = getStripeClient();
const supabase = createPrivilegedSupabaseClient();

export async function POST(req: NextRequest) {
  const body = await req.text();
  const headersList = await headers();
  const signature = headersList.get("stripe-signature");

  if (!signature) {
    return NextResponse.json(
      { error: "Missing stripe signature" },
      { status: 400 },
    );
  }

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      STRIPE_WEBHOOK_SECRET,
    );
  } catch (error) {
    logger.error("Webhook signature verification failed:", error);
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }

  try {
    switch (event.type) {
      case "checkout.session.completed": {
        const session = event.data.object as Stripe.Checkout.Session;

        const { data: purchaseIntent, error: fetchError } = await supabase
          .from("purchase_intents")
          .select("*")
          .eq("stripe_session_id", session.id)
          .single();

        if (fetchError || !purchaseIntent) {
          const userId = session.client_reference_id;
          const orgId = session.metadata?.orgId;
          const packageId = session.metadata?.packageId;
          const credits = parseInt(session.metadata?.credits || "0");

          if (!userId || !packageId || !credits) {
            logger.error("Missing required data in webhook:", { session });
            return NextResponse.json(
              { error: "Missing data" },
              { status: 400 },
            );
          }

          const rpcFunction = orgId
            ? "add_organization_credits"
            : "add_credits";
          const rpcParams = orgId
            ? {
                p_org_id: orgId,
                p_user_id: userId,
                p_amount: credits,
                p_transaction_type: "purchase",
                p_metadata: {
                  stripe_session_id: session.id,
                  stripe_payment_intent: extractIntentString(
                    session.payment_intent,
                  ),
                  package_id: packageId,
                  recovered: true,
                },
              }
            : {
                p_user_id: userId,
                p_amount: credits,
                p_transaction_type: "purchase",
                p_metadata: {
                  stripe_session_id: session.id,
                  stripe_payment_intent: extractIntentString(
                    session.payment_intent,
                  ),
                  package_id: packageId,
                  recovered: true,
                },
              };

          const { error: creditError } = await supabase.rpc(
            rpcFunction,
            rpcParams,
          );

          if (creditError) {
            logger.error("Failed to add credits (recovery):", creditError);
            return NextResponse.json(
              { error: "Failed to add credits" },
              { status: 500 },
            );
          }

          logger.info(
            `Credits added via recovery: ${credits} for ${orgId ? `org ${orgId}` : `user ${userId}`}`,
          );
        } else {
          const { error: updateError } = await supabase
            .from("purchase_intents")
            .update({
              status: "completed",
              completed_at: new Date().toISOString(),
              metadata: {
                ...JSON.parse(JSON.stringify(purchaseIntent.metadata || {})),
                stripe_payment_intent: extractIntentString(
                  session.payment_intent,
                ),
                stripe_payment_status: session.payment_status,
              },
            })
            .eq("id", purchaseIntent.id);

          if (updateError) {
            logger.error("Failed to update purchase intent:", updateError);
          }

          const rpcFunction = purchaseIntent.org_id
            ? "add_organization_credits"
            : "add_credits";
          const rpcParams = purchaseIntent.org_id
            ? {
                p_org_id: purchaseIntent.org_id,
                p_user_id: purchaseIntent.user_id,
                p_amount: purchaseIntent.credits_amount,
                p_transaction_type: "purchase",
                p_metadata: {
                  stripe_session_id: session.id,
                  stripe_payment_intent: extractIntentString(
                    session.payment_intent,
                  ),
                  purchase_intent_id: purchaseIntent.id,
                  package_id: purchaseIntent.package_id,
                },
              }
            : {
                p_user_id: purchaseIntent.user_id,
                p_amount: purchaseIntent.credits_amount,
                p_transaction_type: "purchase",
                p_metadata: {
                  stripe_session_id: session.id,
                  stripe_payment_intent: extractIntentString(
                    session.payment_intent,
                  ),
                  purchase_intent_id: purchaseIntent.id,
                  package_id: purchaseIntent.package_id,
                },
              };

          const { error: creditError } = await supabase.rpc(
            rpcFunction,
            rpcParams,
          );

          if (creditError) {
            logger.error("Failed to add credits:", creditError);
            return NextResponse.json(
              { error: "Failed to add credits" },
              { status: 500 },
            );
          }

          logger.info(
            `Credits added: ${purchaseIntent.credits_amount} for ${purchaseIntent.org_id ? `org ${purchaseIntent.org_id}` : `user ${purchaseIntent.user_id}`}`,
          );
        }

        break;
      }

      case "checkout.session.expired": {
        const session = event.data.object as Stripe.Checkout.Session;

        const { error } = await supabase
          .from("purchase_intents")
          .update({ status: "expired" })
          .eq("stripe_session_id", session.id);

        if (error) {
          logger.error("Failed to update expired session:", error);
        }
        break;
      }

      default:
        logger.info(`Unhandled event type: ${event.type}`);
    }

    return NextResponse.json({ received: true });
  } catch (error) {
    logger.error("Webhook handler error:", error);
    return NextResponse.json(
      { error: "Webhook handler failed" },
      { status: 500 },
    );
  }
}
