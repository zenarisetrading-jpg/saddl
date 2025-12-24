-- Schema Migration for Impact Analyzer Fix
-- Run this against your database (SQLite or PostgreSQL)

-- ==========================================
-- Step 1: Add new columns to actions_log table
-- ==========================================

-- For SQLite:
ALTER TABLE actions_log ADD COLUMN winner_source_campaign TEXT;
ALTER TABLE actions_log ADD COLUMN new_campaign_name TEXT;
ALTER TABLE actions_log ADD COLUMN before_match_type TEXT;
ALTER TABLE actions_log ADD COLUMN after_match_type TEXT;

-- For PostgreSQL (if using Postgres):
-- ALTER TABLE actions_log ADD COLUMN IF NOT EXISTS winner_source_campaign TEXT;
-- ALTER TABLE actions_log ADD COLUMN IF NOT EXISTS new_campaign_name TEXT;
-- ALTER TABLE actions_log ADD COLUMN IF NOT EXISTS before_match_type TEXT;
-- ALTER TABLE actions_log ADD COLUMN IF NOT EXISTS after_match_type TEXT;

-- ==========================================
-- Step 2: Verify migration
-- ==========================================

-- Check that columns were added:
-- SQLite:
PRAGMA table_info(actions_log);

-- PostgreSQL:
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'actions_log';

-- ==========================================
-- Step 3: (Optional) Backfill existing data
-- ==========================================

-- If you have existing harvest actions and want to infer winner source:
-- This is a best-effort backfill - new data will have correct values

-- Update harvest actions to populate campaign name as "new_campaign_name"
UPDATE actions_log 
SET new_campaign_name = campaign_name
WHERE action_type = 'harvest' 
  AND new_campaign_name IS NULL;

-- Note: winner_source_campaign cannot be reliably backfilled
-- It will be NULL for old actions, which is fine (fallback logic handles it)

-- ==========================================
-- Verification Query
-- ==========================================

-- Check sample of updated records:
SELECT 
    action_type,
    target_text,
    campaign_name,
    winner_source_campaign,
    new_campaign_name,
    before_match_type,
    after_match_type,
    action_date
FROM actions_log
WHERE action_date >= date('now', '-30 days')
LIMIT 10;
