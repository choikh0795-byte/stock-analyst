-- Migration: Add unique constraint to asset_search_index table
-- Date: 2026-01-06
-- Description: Add unique constraint on (ticker, asset_type) to support bulk upsert

-- Step 1: Remove duplicate rows (if any)
-- Keep the most recent record for each (ticker, asset_type) pair
DELETE FROM asset_search_index
WHERE id NOT IN (
    SELECT MAX(id)
    FROM asset_search_index
    GROUP BY ticker, asset_type
);

-- Step 2: Create unique index
-- Note: This creates a unique constraint on (ticker, asset_type)
CREATE UNIQUE INDEX IF NOT EXISTS uq_asset_ticker_type
ON asset_search_index (ticker, asset_type);

-- Verify the constraint
SELECT
    indexname,
    indexdef
FROM
    pg_indexes
WHERE
    tablename = 'asset_search_index'
    AND indexname = 'uq_asset_ticker_type';
