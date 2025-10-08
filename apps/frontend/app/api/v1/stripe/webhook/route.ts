import { type NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import Stripe from "stripe";
import { getStripeClient, extractIntentString } from "@/lib/clients/stripe";
import { createAdminClient } from "@/lib/supabase/admin";
import { logger } from "@/lib/logger";
import { STRIPE_WEBHOOK_SECRET } from "@/lib/config";
import { withPostHogTracking } from "@/lib/clients/posthog";

const stripe = getStripeClient();
const supabase = createAdminClient();

async function addCreditsToOrganization(
  orgId: string,
  userId: string,
  credits: number,
  sessionId: string,
  paymentIntent: string | Stripe.PaymentIntent | null,
  packageId: string,
  isRecovery: boolean,
  purchaseIntentId?: string,
): Promise<void> {
  const { data: currentCredits, error: fetchCreditsError } = await supabase
    .from("organization_credits")
    .select("credits_balance")
    .eq("org_id", orgId)
    .single();

  if (fetchCreditsError) {
    logger.error(
      `Failed to fetch credits ${isRecovery ? "(recovery)" : ""}:`,
      fetchCreditsError,
    );
    throw new Error("Failed to fetch credits");
  }

  const newBalance = currentCredits.credits_balance + credits;

  const { error: creditsUpdateError } = await supabase
    .from("organization_credits")
    .update({
      credits_balance: newBalance,
      updated_at: new Date().toISOString(),
    })
    .eq("org_id", orgId);

  if (creditsUpdateError) {
    logger.error(
      `Failed to update credits ${isRecovery ? "(recovery)" : ""}:`,
      creditsUpdateError,
    );
    throw new Error("Failed to update credits");
  }

  const transactionMetadata: Record<string, any> = {
    stripe_session_id: sessionId,
    stripe_payment_intent: extractIntentString(paymentIntent),
    package_id: packageId,
  };

  if (isRecovery) {
    transactionMetadata.recovered = true;
  } else if (purchaseIntentId) {
    transactionMetadata.purchase_intent_id = purchaseIntentId;
  }

  const { error: transactionError } = await supabase
    .from("organization_credit_transactions")
    .insert({
      org_id: orgId,
      user_id: userId,
      amount: credits,
      transaction_type: "purchase",
      metadata: transactionMetadata,
      created_at: new Date().toISOString(),
    });

  if (transactionError) {
    logger.error(
      `Failed to log transaction ${isRecovery ? "(recovery)" : ""}:`,
      transactionError,
    );
  }

  logger.info(
    `Credits added${isRecovery ? " via recovery" : ""}: ${credits} for org ${orgId}`,
  );
}

export const POST = withPostHogTracking(async (req: NextRequest) => {
  const body = await req.text();
  const headersList = headers();
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

          if (!userId || !orgId || !packageId || !credits) {
            logger.error("Missing required data in webhook:", { session });
            return NextResponse.json(
              { error: "Missing data" },
              { status: 400 },
            );
          }

          try {
            await addCreditsToOrganization(
              orgId,
              userId,
              credits,
              session.id,
              session.payment_intent,
              packageId,
              true,
            );
          } catch (error) {
            logger.error("Failed to add credits (recovery):", error);
            return NextResponse.json(
              {
                error:
                  error instanceof Error
                    ? error.message
                    : "Failed to add credits",
              },
              { status: 500 },
            );
          }
        } else {
          const { error: intentUpdateError } = await supabase
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

          if (intentUpdateError) {
            logger.error(
              "Failed to update purchase intent:",
              intentUpdateError,
            );
          }

          if (!purchaseIntent.org_id) {
            logger.error("Missing org_id in purchase intent:", purchaseIntent);
            return NextResponse.json(
              { error: "Missing org_id" },
              { status: 400 },
            );
          }

          try {
            await addCreditsToOrganization(
              purchaseIntent.org_id,
              purchaseIntent.user_id,
              purchaseIntent.credits_amount,
              session.id,
              session.payment_intent,
              purchaseIntent.package_id,
              false,
              purchaseIntent.id,
            );
          } catch (error) {
            logger.error("Failed to add credits:", error);
            return NextResponse.json(
              {
                error:
                  error instanceof Error
                    ? error.message
                    : "Failed to add credits",
              },
              { status: 500 },
            );
          }
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

      case "checkout.session.async_payment_failed": {
        const session = event.data.object as Stripe.Checkout.Session;

        const { error } = await supabase
          .from("purchase_intents")
          .update({ status: "failed" })
          .eq("stripe_session_id", session.id);

        if (error) {
          logger.error("Failed to update failed payment session:", error);
        }
        break;
      }

      case "payment_intent.payment_failed": {
        const paymentIntent = event.data.object as Stripe.PaymentIntent;

        const { error } = await supabase
          .from("purchase_intents")
          .update({ status: "failed" })
          .like("metadata->stripe_payment_intent", `${paymentIntent.id}%`);

        if (error) {
          logger.error("Failed to update failed payment intent:", error);
        }
        break;
      }

      case "payment_intent.canceled": {
        const paymentIntent = event.data.object as Stripe.PaymentIntent;

        const { error } = await supabase
          .from("purchase_intents")
          .update({ status: "cancelled" })
          .like("metadata->stripe_payment_intent", `${paymentIntent.id}%`);

        if (error) {
          logger.error("Failed to update cancelled payment intent:", error);
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
});
