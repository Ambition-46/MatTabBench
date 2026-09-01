#!/usr/bin/env python3
"""
Fix MySQL triggers → PostgreSQL (streaming).
Also clean up remaining delimiter comments.
"""
import re
import sys

RE_CREATE_TRIGGER = re.compile(
    r'CREATE\s+TRIGGER\s+"(\w+)"\s+'
    r'(BEFORE|AFTER)\s+(UPDATE|INSERT|DELETE)\s+'
    r'ON\s+"(\w+)"\s+FOR\s+EACH\s+ROW\s+'
    r'SET\s+(.*?);\s*$',
    re.IGNORECASE,
)

RE_DELIM_COMMENT = re.compile(
    r'^--\s*delimiter\s+.*$', re.IGNORECASE
)


def process_stream(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as fin:
        with open(output_path, 'w', encoding='utf-8') as fout:
            for line in fin:
                # Skip delimiter comment lines
                if RE_DELIM_COMMENT.match(line):
                    continue

                # Detect MySQL CREATE TRIGGER and convert
                m = RE_CREATE_TRIGGER.match(line.strip())
                if m:
                    trig_name = m.group(1)
                    timing = m.group(2)
                    event = m.group(3)
                    tbl = m.group(4)
                    body = m.group(5).strip()
                    fn = f"{trig_name}_fn"

                    fout.write(f'\n-- Converted trigger: {trig_name}\n')
                    fout.write(
                        f'CREATE OR REPLACE FUNCTION "{fn}"() '
                        f'RETURNS trigger AS $$\n'
                        f'BEGIN\n'
                        f'  {body};\n'
                        f'  RETURN NEW;\n'
                        f'END;\n'
                        f'$$ LANGUAGE plpgsql;\n\n'
                    )
                    fout.write(
                        f'CREATE TRIGGER "{trig_name}" '
                        f'{timing} {event} ON "{tbl}" '
                        f'FOR EACH ROW EXECUTE FUNCTION "{fn}"();\n'
                    )
                    continue

                fout.write(line)

    print(f'Trigger conversion done: {input_path} → {output_path}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python fix_triggers.py <input.sql> [output.sql]')
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else inp.replace('.sql', '_final.sql')
    process_stream(inp, out)
