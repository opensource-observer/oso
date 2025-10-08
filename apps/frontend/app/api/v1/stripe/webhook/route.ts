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

          const { data: currentCredits, error: fetchCreditsError } =
            await supabase
              .from("organization_credits")
              .select("credits_balance")
              .eq("org_id", orgId)
              .single();

          if (fetchCreditsError) {
            logger.error(
              "Failed to fetch credits (recovery):",
              fetchCreditsError,
            );
            return NextResponse.json(
              { error: "Failed to fetch credits" },
              { status: 500 },
            );
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
              "Failed to update credits (recovery):",
              creditsUpdateError,
            );
            return NextResponse.json(
              { error: "Failed to update credits" },
              { status: 500 },
            );
          }

          const { error: transactionError } = await supabase
            .from("organization_credit_transactions")
            .insert({
              org_id: orgId,
              user_id: userId,
              amount: credits,
              transaction_type: "purchase",
              metadata: {
                stripe_session_id: session.id,
                stripe_payment_intent: extractIntentString(
                  session.payment_intent,
                ),
                package_id: packageId,
                recovered: true,
              },
              created_at: new Date().toISOString(),
            });

          if (transactionError) {
            logger.error(
              "Failed to log transaction (recovery):",
              transactionError,
            );
          }

          logger.info(
            `Credits added via recovery: ${credits} for org ${orgId}`,
          );
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

          const { data: currentCredits, error: fetchCreditsError } =
            await supabase
              .from("organization_credits")
              .select("credits_balance")
              .eq("org_id", purchaseIntent.org_id)
              .single();

          if (fetchCreditsError) {
            logger.error("Failed to fetch credits:", fetchCreditsError);
            return NextResponse.json(
              { error: "Failed to fetch credits" },
              { status: 500 },
            );
          }

          const newBalance =
            currentCredits?.credits_balance + purchaseIntent.credits_amount;

          const { error: creditsUpdateError } = await supabase
            .from("organization_credits")
            .update({
              credits_balance: newBalance,
              updated_at: new Date().toISOString(),
            })
            .eq("org_id", purchaseIntent.org_id);

          if (creditsUpdateError) {
            logger.error("Failed to update credits:", creditsUpdateError);
            return NextResponse.json(
              { error: "Failed to update credits" },
              { status: 500 },
            );
          }

          const { error: transactionError } = await supabase
            .from("organization_credit_transactions")
            .insert({
              org_id: purchaseIntent.org_id,
              user_id: purchaseIntent.user_id,
              amount: purchaseIntent.credits_amount,
              transaction_type: "purchase",
              metadata: {
                stripe_session_id: session.id,
                stripe_payment_intent: extractIntentString(
                  session.payment_intent,
                ),
                purchase_intent_id: purchaseIntent.id,
                package_id: purchaseIntent.package_id,
              },
              created_at: new Date().toISOString(),
            });

          if (transactionError) {
            logger.error("Failed to log transaction:", transactionError);
          }

          logger.info(
            `Credits added: ${purchaseIntent.credits_amount} for org ${purchaseIntent.org_id}`,
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
