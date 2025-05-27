CREATE TABLE IF NOT EXISTS public.purchase_intents (
  id UUID DEFAULT extensions.uuid_generate_v4() PRIMARY KEY,
  user_id UUID NOT NULL,
  stripe_session_id TEXT NOT NULL UNIQUE,
  package_id TEXT NOT NULL,
  credits_amount INTEGER NOT NULL,
  price_cents INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  completed_at TIMESTAMPTZ,
  metadata JSONB,
  CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES auth.users(id),
  CONSTRAINT valid_status CHECK (status IN ('pending', 'completed', 'cancelled', 'expired'))
);

CREATE INDEX IF NOT EXISTS idx_purchase_intents_user_id ON public.purchase_intents(user_id);
CREATE INDEX IF NOT EXISTS idx_purchase_intents_stripe_session_id ON public.purchase_intents(stripe_session_id);
CREATE INDEX IF NOT EXISTS idx_purchase_intents_status ON public.purchase_intents(status);

ALTER TABLE public.purchase_intents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own purchase intents" ON public.purchase_intents
  FOR SELECT USING (auth.uid() = user_id);
