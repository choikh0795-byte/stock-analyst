-- PostgreSQL 스키마 수정: search_tokens 컬럼 타입 변경
-- character varying[] -> TEXT[]

ALTER TABLE asset_search_index
ALTER COLUMN search_tokens TYPE TEXT[]
USING search_tokens::TEXT[];

