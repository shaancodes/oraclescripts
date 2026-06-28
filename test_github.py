import requests, datetime
r = requests.get('https://api.github.com/repos/tilak999/NSE-Data-bank/git/trees/main?recursive=1').json()
files = [f['path'] for f in r.get('tree', []) if f['path'].startswith('data/sec_bhavdata_full_')]
parsed = []
for f in files:
    date_str = f.split('_')[-1].split('.')[0]
    try:
        parsed.append((datetime.datetime.strptime(date_str, '%d%m%Y'), f))
    except Exception:
        pass
parsed.sort(key=lambda x: x[0])
print([x[1] for x in parsed[-2:]])
