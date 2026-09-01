import json
import os

p = os.path.join(os.getcwd(), 'sql_nl_test_samples_500.json')
if not os.path.exists(p):
    print('source not found:', p)
    raise SystemExit(1)

with open(p, 'r', encoding='utf-8') as f:
    data = json.load(f)

out = [s for s in data if isinstance(s.get('result'), list) and len(s.get('result')) == 0]

out_path = os.path.join(os.getcwd(), 'empty_results_samples.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print('Exported', len(out), 'samples to', out_path)
