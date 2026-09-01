#!/usr/bin/env python3
"""
Fix remaining MySQL-specific DDL issues (streaming version 2).
"""
import re
import sys

RE_ENUM = re.compile(r"enum\('object','operate','result'\)", re.IGNORECASE)
RE_INLINE_IDX = re.compile(
    r',?\s*INDEX\s+"(\w+)"\s*\(([^)]+)\)', re.IGNORECASE
)
RE_INLINE_UNIQ = re.compile(
    r',?\s*UNIQUE\s+INDEX\s+"(\w+)"\s*\(([^)]+)\)', re.IGNORECASE
)
RE_COL_PFX = re.compile(r'"(\w+)"\s*\(\s*(\d+)\s*\)')
RE_ON_UPDATE = re.compile(
    r'\s+ON\s+UPDATE\s+CURRENT_TIMESTAMP\s*(?:\(\s*\d*\s*\))?', re.IGNORECASE
)
RE_DROP_TRIGGER = re.compile(
    r'DROP\s+TRIGGER\s+IF\s+EXISTS\s+"(\w+)"', re.IGNORECASE
)
RE_CREATE_TRIGGER = re.compile(
    r'CREATE\s+TRIGGER\s+"(\w+)"\s+'
    r'(BEFORE|AFTER)\s+(UPDATE|INSERT|DELETE)\s+'
    r'ON\s+"(\w+)"\s+FOR\s+EACH\s+ROW\s+'
    r'SET\s+(.*?);',
    re.IGNORECASE,
)
RE_CREATE_TABLE = re.compile(r'CREATE\s+TABLE\s+"(\w+)"', re.IGNORECASE)


def process_create_table(body, table_name):
    """Process a complete CREATE TABLE body, return (new_body, extra_statements)."""
    extra = []

    # 0. Fix ON UPDATE CURRENT_TIMESTAMP (belt-and-suspenders for sed)
    body = RE_ON_UPDATE.sub('', body)

    # 0b. Pre-process: fix ALL column prefixes BEFORE extracting indexes.
    # This prevents nested parens from breaking the index extraction regex.
    body = RE_COL_PFX.sub(r'"\1"', body)

    # 1. Fix ENUM
    if RE_ENUM.search(body):
        body = RE_ENUM.sub('varchar(20)', body)
        extra.append(
            f'ALTER TABLE "{table_name}" ADD CONSTRAINT '
            f'"chk_{table_name}_bitmap_role" CHECK '
            f'("bitmap_role" IN (\'object\', \'operate\', \'result\'));'
        )

    # 2. UNIQUE INDEX → UNIQUE constraint
    def conv_uniq(m):
        idx, cols = m.group(1), m.group(2)
        return f',\n  CONSTRAINT "{idx}" UNIQUE ({cols})'

    body = RE_INLINE_UNIQ.sub(conv_uniq, body)

    # 3. INDEX → separate CREATE INDEX
    def conv_idx(m):
        idx, cols = m.group(1), m.group(2)
        extra.append(f'CREATE INDEX "{idx}" ON "{table_name}" ({cols});')
        return ''

    body = RE_INLINE_IDX.sub(conv_idx, body)

    # 4. Clean up
    body = re.sub(r',\s*,', ',', body)
    body = re.sub(r',\s*\n\s*\)', '\n)', body)
    body = re.sub(r'\(\s*,', '(', body)
    body = re.sub(r'\n\s*\n\s*\n', '\n\n', body)

    return body, extra


def process_stream(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as fin:
        with open(output_path, 'w', encoding='utf-8') as fout:
            in_create = False
            table_name = ''
            create_buf = []
            in_trigger_block = False
            trigger_buf = []

            for line in fin:
                # ── Trigger handling ──
                if line.strip().startswith('DROP TRIGGER'):
                    m = RE_DROP_TRIGGER.search(line)
                    if m:
                        name = m.group(1)
                        fout.write(
                            f'DROP TRIGGER IF EXISTS "{name}" ON "value_table";\n'
                        )
                        fout.write(f'DROP FUNCTION IF EXISTS "{name}_fn"();\n')
                        continue
                    fout.write(line)
                    continue

                if line.strip().startswith('delimiter ;'):
                    if in_trigger_block and trigger_buf:
                        full = ' '.join(
                            l.strip()
                            for l in trigger_buf
                            if not l.strip().startswith('--')
                            and l.strip()
                        )
                        m = RE_CREATE_TRIGGER.search(full)
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
                    in_trigger_block = False
                    trigger_buf = []
                    continue

                if in_trigger_block:
                    stripped = line.strip()
                    if stripped and not stripped.startswith('--'):
                        trigger_buf.append(line)
                    continue

                if line.strip().startswith('delimiter ;;'):
                    in_trigger_block = True
                    continue

                if line.strip() == ';;':
                    continue

                # ── CREATE TABLE handling ──
                if line.strip().startswith('CREATE TABLE') and not in_create:
                    m = RE_CREATE_TABLE.search(line)
                    table_name = m.group(1) if m else ''
                    in_create = True
                    create_buf = [line]
                    continue

                if in_create:
                    create_buf.append(line)
                    if line.strip().endswith(');'):
                        full = ''.join(create_buf)
                        new_body, extra = process_create_table(full, table_name)
                        fout.write(new_body)
                        if extra:
                            fout.write('\n')
                            for s in extra:
                                fout.write(s + '\n')
                            fout.write('\n')
                        else:
                            fout.write('\n')
                        in_create = False
                        table_name = ''
                        create_buf = []
                    continue

                # ── Pass through ──
                fout.write(line)

    print(f'Streaming conversion done: {input_path} → {output_path}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python fix_ddl.py <input.sql> [output.sql]')
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else inp.replace('.sql', '_fixed.sql')
    process_stream(inp, out)
