// An enum defining the events that can be tracked in PostHog.
const EVENTS = {
  API_CALL: "api_call",
  DB_WRITE: "supabase_write",
  STRIPE_CHECKOUT: "stripe_checkout",
  INSUFFICIENT_CREDITS: "insufficient_credits",
};

export { EVENTS };
