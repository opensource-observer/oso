-- Create a table for user credits
CREATE TABLE IF NOT EXISTS user_credits (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES auth.users NOT NULL,
  credits_balance INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  UNIQUE (user_id)
);

-- Create a table for credit transactions
CREATE TABLE IF NOT EXISTS credit_transactions (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES auth.users NOT NULL,
  amount INTEGER NOT NULL,
  transaction_type TEXT NOT NULL,
  api_endpoint TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  metadata JSONB
);

-- Set up Row Level Security (RLS)
ALTER TABLE user_credits ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;

-- RLS policies for user_credits
DROP POLICY IF EXISTS "Users can view their own credits" ON user_credits;
CREATE POLICY "Users can view their own credits" ON user_credits
  FOR SELECT USING (auth.uid() = user_id);

-- RLS policies for credit_transactions
DROP POLICY IF EXISTS "Users can view their own transactions" ON credit_transactions;
CREATE POLICY "Users can view their own transactions" ON credit_transactions
  FOR SELECT USING (auth.uid() = user_id);

-- Function to add credits when a new user signs up
CREATE OR REPLACE FUNCTION initialize_user_credits()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO user_credits (user_id, credits_balance)
  VALUES (NEW.id, 100); -- Give new users 100 credits initially
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to initialize credits for new users
DROP TRIGGER IF EXISTS on_auth_user_created_add_credits ON auth.users;
CREATE TRIGGER on_auth_user_created_add_credits
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION initialize_user_credits();

-- Function to deduct credits
CREATE OR REPLACE FUNCTION deduct_credits(
  p_user_id UUID,
  p_amount INTEGER,
  p_transaction_type TEXT,
  p_api_endpoint TEXT DEFAULT NULL,
  p_metadata JSONB DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
  current_balance INTEGER;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM user_credits WHERE user_id = p_user_id) THEN
    INSERT INTO user_credits (user_id, credits_balance)
    VALUES (p_user_id, 0);
    current_balance := 0;
  ELSE
    SELECT credits_balance INTO current_balance
    FROM user_credits
    WHERE user_id = p_user_id
    FOR UPDATE;
  END IF;
  
  IF current_balance < p_amount THEN
    INSERT INTO credit_transactions (
      user_id, 
      amount, 
      transaction_type, 
      api_endpoint, 
      metadata
    ) VALUES (
      p_user_id, 
      0, 
      p_transaction_type || '_failed', 
      p_api_endpoint, 
      jsonb_build_object(
        'error', 'insufficient_credits',
        'requested_amount', p_amount,
        'available_balance', current_balance
      ) || COALESCE(p_metadata, '{}'::jsonb)
    );
    
    RETURN FALSE;
  END IF;
  
  UPDATE user_credits
  SET 
    credits_balance = credits_balance - p_amount,
    updated_at = NOW()
  WHERE user_id = p_user_id;
  
  INSERT INTO credit_transactions (
    user_id, 
    amount, 
    transaction_type, 
    api_endpoint, 
    metadata
  ) VALUES (
    p_user_id, 
    -p_amount, 
    p_transaction_type, 
    p_api_endpoint, 
    p_metadata
  );
  
  RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to add credits
CREATE OR REPLACE FUNCTION add_credits(
  p_user_id UUID,
  p_amount INTEGER,
  p_transaction_type TEXT,
  p_metadata JSONB DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
  IF p_amount <= 0 THEN
    RAISE EXCEPTION 'Credit amount must be positive';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM auth.users WHERE id = p_user_id) THEN
    RAISE EXCEPTION 'User does not exist in auth.users';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM user_credits WHERE user_id = p_user_id) THEN
    INSERT INTO user_credits (user_id, credits_balance)
    VALUES (p_user_id, p_amount);
  ELSE
    UPDATE user_credits
    SET 
      credits_balance = credits_balance + p_amount,
      updated_at = NOW()
    WHERE user_id = p_user_id;
  END IF;
  
  INSERT INTO credit_transactions (
    user_id, 
    amount, 
    transaction_type, 
    metadata
  ) VALUES (
    p_user_id, 
    p_amount, 
    p_transaction_type, 
    p_metadata
  );
  
  RETURN TRUE;
EXCEPTION
  WHEN OTHERS THEN
    BEGIN
      INSERT INTO credit_transactions (
        user_id, 
        amount, 
        transaction_type, 
        metadata
      ) VALUES (
        p_user_id, 
        0, 
        p_transaction_type || '_error', 
        jsonb_build_object('error', SQLERRM) || COALESCE(p_metadata, '{}'::jsonb)
      );
    EXCEPTION
      WHEN OTHERS THEN
        NULL;
    END;
    
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user credits
CREATE OR REPLACE FUNCTION get_user_credits(p_user_id UUID)
RETURNS INTEGER AS $$
DECLARE
  balance INTEGER;
BEGIN
  SELECT credits_balance INTO balance FROM user_credits
  WHERE user_id = p_user_id;
  
  RETURN COALESCE(balance, 0);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON user_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at ON credit_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_transaction_type ON credit_transactions(transaction_type);
