-- Users table
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT UNIQUE NOT NULL,
  username TEXT,
  credits INT DEFAULT 0,
  referral_code TEXT UNIQUE,
  referrer_id BIGINT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Lookup history table
CREATE TABLE lookup_history (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(user_id),
  lookup_type TEXT NOT NULL,
  search_query TEXT,
  search_id TEXT UNIQUE,
  credit_cost INT,
  status TEXT,
  timestamp TIMESTAMP DEFAULT NOW()
);

-- Credit transactions table
CREATE TABLE credit_transactions (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(user_id),
  amount INT,
  reason TEXT,
  timestamp TIMESTAMP DEFAULT NOW()
);

-- Payment requests table
CREATE TABLE payment_requests (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(user_id),
  credit_amount INT,
  utr TEXT,
  screenshot_url TEXT,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW()
);

-- Referrals table
CREATE TABLE referrals (
  id BIGSERIAL PRIMARY KEY,
  referrer_id BIGINT REFERENCES users(user_id),
  referred_user_id BIGINT REFERENCES users(user_id),
  credit_reward INT,
  timestamp TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_user_id ON users(user_id);
CREATE INDEX idx_lookup_user ON lookup_history(user_id);
CREATE INDEX idx_lookup_timestamp ON lookup_history(timestamp);
CREATE INDEX idx_payment_user ON payment_requests(user_id);
CREATE INDEX idx_payment_status ON payment_requests(status);
CREATE INDEX idx_referral_code ON users(referral_code);
