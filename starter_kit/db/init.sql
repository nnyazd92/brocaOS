-- Initial schema for Broca starter with pgvector

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS memories (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  text TEXT,
  meta JSONB,
  embedding vector(1536),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_memories_session ON memories(session_id);
-- ivfflat index for faster vector similarity; requires enough rows to be effective
CREATE INDEX IF NOT EXISTS idx_memories_embedding ON memories USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
