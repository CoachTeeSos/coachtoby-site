import json

with open('/data/data/com.termux/files/home/.hermes/coachtoby-site/bot/tmp/airtable_all.json') as f:
    d = json.load(f)

records = d.get('records', [])
print(f'Total records: {len(records)}')

# Get all unique field names
fields = set()
for r in records:
    fields.update(r.get('fields', {}).keys())
print(f'All fields: {sorted(fields)}')

# Show unique values for select fields
levels = set()
statuses = set()
sources = set()
interests = set()
for r in records:
    f = r.get('fields', {})
    if f.get('Level'): levels.add(f['Level'])
    if f.get('Status'): statuses.add(f['Status'])
    if f.get('Source'): sources.add(f['Source'])
    if f.get('Interest'): interests.add(f['Interest'])

print(f'Level values: {sorted(levels)}')
print(f'Status values: {sorted(statuses)}')
print(f'Source values: {sorted(sources)}')
print(f'Interest values: {sorted(interests)}')
