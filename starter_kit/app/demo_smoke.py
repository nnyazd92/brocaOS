"""Demo script that seeds a session with memories and queries them using the API modules (calls DB directly)."""
from . import db, embeddings
import uuid

def demo():
    user_id = 'demo_user'
    session_id = db.create_session(user_id)
    print('session', session_id)
    items = [
        {'id': str(uuid.uuid4()), 'text': 'Buy milk and eggs from the grocery store', 'meta': {'tag': 'todo'}},
        {'id': str(uuid.uuid4()), 'text': 'Discuss Q4 marketing plan with the team', 'meta': {'tag': 'work'}},
        {'id': str(uuid.uuid4()), 'text': 'Remember to call the dentist to reschedule', 'meta': {'tag': 'personal'}},
    ]
    # embed and upsert
    for it in items:
        it['embedding'] = embeddings.embed_text(it['text'])
    cnt = db.upsert_memories(session_id, items)
    print('upserted', cnt)
    # query
    q = 'schedule appointment with dentist'
    qvec = embeddings.embed_text(q)
    res = db.query_memories(session_id, qvec, top=3)
    print('query results for:', q)
    for r in res:
        print(r['score'], r['text'])

if __name__ == '__main__':
    demo()
