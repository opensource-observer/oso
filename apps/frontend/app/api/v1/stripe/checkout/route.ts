import { type NextRequest, NextResponse } from "next/server";
import {
  getStripeClient,
  CREDIT_PACKAGES,
  CreditPackageId,
  extractIntentString,
} from "@/lib/clients/stripe";
import { getUser } from "@/lib/auth/auth";
import { createAdminClient } from "@/lib/supabase/admin";
import { logger } from "@/lib/logger";
import { trackServerEvent } from "@/lib/analytics/track";
import { EVENTS } from "@/lib/types/posthog";
import { DOMAIN, STRIPE_PUBLISHABLE_KEY } from "@/lib/config";

const stripe = getStripeClient();
const supabase = createAdminClient();

export async function POST(req: NextRequest) {
  try {
    const user = await getUser(req);
    await using tracker = trackServerEvent(user);

    if (user.role === "anonymous") {
      return NextResponse.json(
        { error: "Authentication required" },
        { status: 401 },
      );
    }

    const body = await req.json();
    const { packageId } = body as { packageId: CreditPackageId };

    const creditPackage = CREDIT_PACKAGES.find((p) => p.id === packageId);
    if (!creditPackage) {
      return NextResponse.json(
        { error: "Invalid package selected" },
        { status: 400 },
      );
    }

    const PROTOCOL = DOMAIN.includes("localhost") ? "http" : "https";

    const session = await stripe.checkout.sessions.create({
      payment_method_types: ["card"],
      line_items: [
        {
          price_data: {
            currency: "usd",
            product_data: {
              name: creditPackage.name,
              description: `${creditPackage.credits} API credits for Open Source Observer`,
            },
            unit_amount: creditPackage.price,
          },
          quantity: 1,
        },
      ],
      mode: "payment",
      success_url: `${PROTOCOL}://${DOMAIN}/billing?purchase=success&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${PROTOCOL}://${DOMAIN}/billing?purchase=cancelled`,
      client_reference_id: user.userId,
      metadata: {
        userId: user.userId,
        packageId: creditPackage.id,
        credits: creditPackage.credits.toString(),
      },
    });

    const { error: dbError } = await supabase.from("purchase_intents").insert({
      user_id: user.userId,
      stripe_session_id: session.id,
      package_id: creditPackage.id,
      credits_amount: creditPackage.credits,
      price_cents: creditPackage.price,
      status: "pending",
      metadata: {
        stripe_payment_intent: extractIntentString(session.payment_intent),
        user_email: user.email,
      },
    });

    if (dbError) {
      logger.error("Failed to store purchase intent:", dbError);
    }

    tracker.track(EVENTS.API_CALL, {
      type: "stripe_checkout_create",
      packageId: creditPackage.id,
      credits: creditPackage.credits,
      price: creditPackage.price,
    });

    return NextResponse.json({
      sessionId: session.id,
      publishableKey: STRIPE_PUBLISHABLE_KEY,
      url: session.url,
    });
  } catch (error) {
    logger.error("Error creating checkout session:", error);
    return NextResponse.json(
      { error: "Failed to create checkout session" },
      { status: 500 },
    );
  }
}
