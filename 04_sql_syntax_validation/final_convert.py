#!/usr/bin/env python3
"""
Comprehensive MySQL → PostgreSQL conversion (single pass, streaming).
Handles: DDL (table/index/enum/column-prefix), FUNCTION, TRIGGER.
"""
import re
import sys

# ── DDL Patterns ──
RE_CREATE_TABLE = re.compile(r'CREATE\s+TABLE\s+"(\w+)"', re.IGNORECASE)
RE_ENUM = re.compile(r"enum\('object','operate','result'\)", re.IGNORECASE)
RE_INLINE_IDX = re.compile(r',?\s*INDEX\s+"(\w+)"\s*\(([^)]+)\)', re.IGNORECASE)
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
RE_DROP_FUNCTION = re.compile(
    r'DROP\s+FUNCTION\s+IF\s+EXISTS\s+"(\w+)"', re.IGNORECASE
)
RE_CREATE_FUNC_HEADER = re.compile(
    r'CREATE\s+FUNCTION\s+"(\w+)"', re.IGNORECASE
)
RE_CREATE_TRIGGER = re.compile(
    r'CREATE\s+TRIGGER\s+"(\w+)"\s+'
    r'(BEFORE|AFTER)\s+(UPDATE|INSERT|DELETE)\s+'
    r'ON\s+"(\w+)"\s+FOR\s+EACH\s+ROW\s+'
    r'SET\s+(.*)',
    re.IGNORECASE,
)
RE_END_OF_TRIGGER = re.compile(r'\s*;\s*--\s*end\s+of\s+trigger')


def process_table_ddl(body, table_name):
    """Fix CREATE TABLE body."""
    extra = []
    body = RE_ON_UPDATE.sub('', body)
    body = RE_COL_PFX.sub(r'"\1"', body)

    if RE_ENUM.search(body):
        body = RE_ENUM.sub('varchar(20)', body)
        extra.append(
            f'ALTER TABLE "{table_name}" ADD CONSTRAINT '
            f'"chk_{table_name}_bitmap_role" CHECK '
            f'("bitmap_role" IN (\'object\', \'operate\', \'result\'));'
        )

    def conv_uniq(m):
        return f',\n  CONSTRAINT "{m.group(1)}" UNIQUE ({m.group(2)})'
    body = RE_INLINE_UNIQ.sub(conv_uniq, body)

    def conv_idx(m):
        extra.append(
            f'CREATE INDEX "{m.group(1)}" ON "{table_name}" ({m.group(2)});'
        )
        return ''
    body = RE_INLINE_IDX.sub(conv_idx, body)

    body = re.sub(r',\s*,', ',', body)
    body = re.sub(r',\s*\n\s*\)', '\n)', body)
    body = re.sub(r'\(\s*,', '(', body)
    body = re.sub(r'\n\s*\n\s*\n', '\n\n', body)
    return body, extra


def convert_mysql_function(name, lines):
    """
    Convert MySQL function body to PostgreSQL PL/pgSQL.
    `lines` are from BEGIN (exclusive) to END (exclusive).
    """
    body = '\n'.join(lines)

    # ---- Step 1: CAST(x AS UNSIGNED) → x::bigint (BEFORE removing UNSIGNED) ----
    body = re.sub(
        r'CAST\s*\(\s*(\w+)\s+AS\s+UNSIGNED\s*\)',
        r'\1::bigint',
        body,
        flags=re.IGNORECASE,
    )

    # ---- Step 2: LOCATE(x, y) → position(x in y) ----
    # More robust: match LOCATE(expr1, expr2) where expr1 is quoted or word
    body = re.sub(
        r'\bLOCATE\s*\(\s*("[^"]*"|\'[^\']*\'|\w+)\s*,\s*(\w+)\s*\)',
        r'position(\1 in \2)',
        body,
        flags=re.IGNORECASE,
    )

    # ---- Step 3: INSERT(str, pos, len, new) → overlay(str placing new from pos for len) ----
    body = re.sub(
        r'\bINSERT\s*\(\s*(\w+)\s*,\s*(\w+)\s*,\s*(\d+)\s*,\s*([^)]+)\s*\)',
        r'overlay(\1 placing \4 from \2 for \3)',
        body,
        flags=re.IGNORECASE,
    )

    # ---- Step 4: REGEXP → ~ ----
    body = re.sub(
        r'(\w+)\s+REGEXP\s+',
        r'\1 ~ ',
        body,
        flags=re.IGNORECASE,
    )

    # ---- Step 5: WHILE ... DO → WHILE ... LOOP ----
    body = re.sub(r'\bWHILE\b(.+?)\bDO\b', r'WHILE\1LOOP', body, flags=re.IGNORECASE)
    body = re.sub(r'\bEND\s+WHILE\b', 'END LOOP', body, flags=re.IGNORECASE)

    # ---- Step 6: SET var = expr → var := expr ----
    body = re.sub(r'\bSET\s+(\w+)\s*=', r'\1 :=', body)

    # ---- Step 7: Handle DECLARE section ----
    # Collect all DECLARE lines, convert them, output a single DECLARE block
    decl_vars = []
    non_decl_lines = []
    for line in body.split('\n'):
        m = re.match(
            r'\s*DECLARE\s+(\w+)\s+(\S+(?:\s+\S+)*?)\s*'
            r'(?:DEFAULT\s+(.+?))?\s*;\s*$',
            line,
            flags=re.IGNORECASE,
        )
        if m:
            var_name = m.group(1)
            var_type = m.group(2).strip()
            default_val = m.group(3)
            # Remove UNSIGNED from type
            var_type = re.sub(r'\bUNSIGNED\b', '', var_type, flags=re.IGNORECASE).strip()
            if default_val:
                decl_vars.append(f'    {var_name} {var_type} := {default_val};')
            else:
                decl_vars.append(f'    {var_name} {var_type};')
        else:
            # Keep non-DECLARE lines (clean them up)
            stripped = line.strip()
            if stripped:
                non_decl_lines.append(line)

    # Build PG function body
    pg_lines = []
    if decl_vars:
        pg_lines.append('DECLARE')
        pg_lines.extend(decl_vars)
    pg_lines.append('BEGIN')

    # Add non-declare lines (body)
    for line in non_decl_lines:
        stripped = line.strip()
        if stripped:
            # Clean up standalone UNSIGNED
            stripped = re.sub(r'\bUNSIGNED\b', '', stripped, flags=re.IGNORECASE)
            # Fix SUBSTRING → lowercase (PG accepts both)
            pg_lines.append(f'    {stripped}')
        else:
            pg_lines.append('')

    pg_lines.append('END;')

    body_final = '\n'.join(pg_lines)

    sql = (
        f'\nCREATE OR REPLACE FUNCTION "{name}"(ids_text TEXT)\n'
        f'RETURNS varchar(1024) AS $$\n'
        f'{body_final}\n'
        f'$$ LANGUAGE plpgsql IMMUTABLE;\n'
    )
    return sql


def convert_mysql_trigger(name, timing, event, table, body):
    """Convert MySQL trigger body to PL/pgSQL trigger function."""
    fn = f"{name}_fn"
    # Fix assignment: NEW.xxx = expr → NEW.xxx := expr
    body = re.sub(r'NEW\.(\w+)\s*=\s*\(', r'NEW.\1 := (', body)
    return (
        f'\n-- Converted trigger: {name}\n'
        f'CREATE OR REPLACE FUNCTION "{fn}"()\n'
        f'RETURNS trigger AS $$\n'
        f'BEGIN\n'
        f'  {body};\n'
        f'  RETURN NEW;\n'
        f'END;\n'
        f'$$ LANGUAGE plpgsql;\n\n'
        f'CREATE TRIGGER "{name}"\n'
        f'{timing} {event} ON "{table}"\n'
        f'FOR EACH ROW EXECUTE FUNCTION "{fn}"();\n'
    )


def process_stream(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as fin:
        with open(output_path, 'w', encoding='utf-8') as fout:
            # ── State ──
            in_create_table = False
            table_name = ''
            create_buf = []

            # Function block state: DROP FUNCTION → ... → END
            in_func_block = False
            func_name = ''
            func_body_lines = []  # lines between BEGIN and END
            awaiting_begin = False  # waiting for BEGIN keyword
            in_func_body = False    # between BEGIN and END

            # Trigger block state: DROP TRIGGER → CREATE TRIGGER
            in_trig_block = False
            trig_name = ''

            for line in fin:
                stripped = line.strip()

                # ── Filter stray end-of-trigger markers ──
                if RE_END_OF_TRIGGER.match(stripped):
                    continue
                if stripped == ';;':
                    continue
                if stripped.startswith('delimiter'):
                    continue

                # ── DROP FUNCTION ──
                if stripped.startswith('DROP FUNCTION'):
                    m = RE_DROP_FUNCTION.search(stripped)
                    if m:
                        fout.write(f'-- Original: {stripped}\n')
                        in_func_block = True
                        func_name = m.group(1)
                        func_body_lines = []
                        awaiting_begin = True
                        in_func_body = False
                        continue
                    fout.write(line)
                    continue

                # ── DROP TRIGGER ──
                if stripped.startswith('DROP TRIGGER'):
                    m = RE_DROP_TRIGGER.search(stripped)
                    if m:
                        name = m.group(1)
                        fout.write(
                            f'DROP TRIGGER IF EXISTS "{name}" ON "value_table";\n'
                        )
                        fout.write(f'DROP FUNCTION IF EXISTS "{name}_fn"();\n')
                        in_trig_block = True
                        trig_name = name
                        continue
                    fout.write(line)
                    continue

                # ── Inside function block ──
                if in_func_block:
                    if awaiting_begin:
                        # Skip all lines until we see BEGIN (exclusive)
                        if re.match(r'^\s*BEGIN\s*$', stripped, re.IGNORECASE):
                            awaiting_begin = False
                            in_func_body = True
                        continue

                    if in_func_body:
                        if re.match(r'^\s*END\s*$', stripped, re.IGNORECASE):
                            # End of function body
                            pg_func = convert_mysql_function(
                                func_name, func_body_lines
                            )
                            fout.write(pg_func)
                            fout.write('\n')
                            in_func_block = False
                            func_name = ''
                            func_body_lines = []
                            awaiting_begin = False
                            in_func_body = False
                            continue
                        func_body_lines.append(line)
                        continue

                    continue

                # ── Inside trigger block ──
                if in_trig_block:
                    m_trig = RE_CREATE_TRIGGER.match(stripped)
                    if m_trig:
                        name = m_trig.group(1)
                        timing = m_trig.group(2)
                        event = m_trig.group(3)
                        tbl = m_trig.group(4)
                        body = m_trig.group(5).strip()
                        pg_trig = convert_mysql_trigger(
                            name, timing, event, tbl, body
                        )
                        fout.write(pg_trig)
                        in_trig_block = False
                        trig_name = ''
                        continue
                    # Skip comments between DROP and CREATE
                    if stripped and not stripped.startswith('--'):
                        pass  # non-comment, non-trigger line
                    continue

                # ── CREATE TABLE ──
                if stripped.startswith('CREATE TABLE') and not in_create_table:
                    m = RE_CREATE_TABLE.search(line)
                    table_name = m.group(1) if m else ''
                    in_create_table = True
                    create_buf = [line]
                    continue

                if in_create_table:
                    create_buf.append(line)
                    if stripped.endswith(');'):
                        full = ''.join(create_buf)
                        new_body, extra = process_table_ddl(full, table_name)
                        fout.write(new_body)
                        if extra:
                            fout.write('\n')
                            for s in extra:
                                fout.write(s + '\n')
                            fout.write('\n')
                        else:
                            fout.write('\n')
                        in_create_table = False
                        table_name = ''
                        create_buf = []
                    continue

                # ── Pass through ──
                fout.write(line)

    print(f'Final conversion done: {input_path} → {output_path}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python final_convert.py <input.sql> [output.sql]')
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else inp.replace('.sql', '_final.sql')
    process_stream(inp, out)
