from broca import BrocaClient

c = BrocaClient(endpoint="http://localhost:8080")
print('health ->', c.health())
s = c.create_session('user-123')
print('session ->', s)

# upsert memory
up = c.memory_upsert(s.get('session_id','anon'), items=[{"id":"m1","text":"User prefers green","meta":{}}])
print('upsert ->', up)

# query memory
q = c.memory_query(s.get('session_id','anon'), query='what color does the user prefer?')
print('query ->', q)

# request an actuator action
req = c.actuator_request(s.get('session_id','anon'), action='create_ticket', payload={"title":"Support needed"})
print('actuator request ->', req)
