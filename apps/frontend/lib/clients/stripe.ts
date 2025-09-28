import Stripe from "stripe";
import { STRIPE_SECRET_KEY } from "@/lib/config";

let stripeClient: Stripe | null = null;

export function getStripeClient(): Stripe {
  if (!stripeClient) {
    stripeClient = new Stripe(STRIPE_SECRET_KEY, {
      apiVersion: "2025-07-30.basil",
    });
  }
  return stripeClient;
}

export const CREDIT_PACKAGES = [
  {
    id: "credits_100",
    name: "100 Credits",
    credits: 100,
    price: 500,
  },
  {
    id: "credits_500",
    name: "500 Credits",
    credits: 500,
    price: 2000,
  },
  {
    id: "credits_1000",
    name: "1,000 Credits",
    credits: 1000,
    price: 3500,
  },
  {
    id: "credits_5000",
    name: "5,000 Credits",
    credits: 5000,
    price: 15000,
  },
] as const;

export const extractIntentString = (
  intent: Stripe.PaymentIntent | string | null,
): string => {
  if (typeof intent === "string") {
    return intent;
  }

  if (
    !intent ||
    typeof intent !== "object" ||
    !("id" in intent) ||
    !("status" in intent)
  ) {
    return "Unknown Intent";
  }

  return `${intent.id} (${intent.status})`;
};

export type CreditPackageId = (typeof CREDIT_PACKAGES)[number]["id"];
