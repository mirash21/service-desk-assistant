-- Изменить размерность вектора с 256 на 3072
ALTER TABLE documents ALTER COLUMN embedding TYPE vector(3072);

-- Обновить функцию match_documents
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(3072),
  match_count int DEFAULT 3,
  filter jsonb DEFAULT '{}'::jsonb
)
RETURNS TABLE (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    id,
    content,
    metadata,
    1 - (embedding <=> query_embedding) AS similarity
  FROM documents
  WHERE metadata @> filter
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;
