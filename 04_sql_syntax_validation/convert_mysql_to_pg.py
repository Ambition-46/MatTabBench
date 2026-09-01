#!/usr/bin/env python3
"""
Convert MySQL dump (Navicat export) to PostgreSQL-compatible SQL.

Usage:
    python convert_mysql_to_pg.py <input.sql> [output.sql]

If output is omitted, writes to <input_basename>_pg.sql in the same directory.
"""

import re
import sys
import os


# ── Patterns ──────────────────────────────────────────────────────────

# Table-level options at end of CREATE TABLE
RE_TABLE_ENGINE = re.compile(
    r"\)\s*ENGINE\s*=\s*InnoDB\s+"
    r"(?:AUTO_INCREMENT\s*=\s*\d+\s*)?"
    r"(?:CHARACTER\s+SET\s*=\s*\w+\s*)?"
    r"(?:COLLATE\s*=\s*\w+\s*)?"
    r"ROW_FORMAT\s*=\s*(?:Dynamic|DYNAMIC)\s*;",
    re.IGNORECASE,
)

# Inline column CHARACTER SET + COLLATE
RE_COL_CHARSET = re.compile(
    r"\s+CHARACTER\s+SET\s+\w+\s+COLLATE\s+\w+",
    re.IGNORECASE,
)

# Standalone COLLATE in column
RE_COL_COLLATE = re.compile(r"\s+COLLATE\s+\w+", re.IGNORECASE)

# USING BTREE
RE_USING_BTREE = re.compile(r"\s+USING\s+BTREE", re.IGNORECASE)

# ON UPDATE CURRENT_TIMESTAMP
RE_ON_UPDATE = re.compile(
    r"\s+ON\s+UPDATE\s+CURRENT_TIMESTAMP(?:\(\d*\))?", re.IGNORECASE
)

# NULL DEFAULT NULL → DEFAULT NULL
RE_NULL_DEFAULT_NULL = re.compile(
    r"\s+NULL\s+DEFAULT\s+NULL", re.IGNORECASE
)

# COMMENT 'xxx' on columns
RE_COMMENT = re.compile(r"\s+COMMENT\s+'[^']*'", re.IGNORECASE)

# int UNSIGNED
RE_INT_UNSIGNED = re.compile(r"\bint\s+UNSIGNED\b", re.IGNORECASE)
# bigint UNSIGNED
RE_BIGINT_UNSIGNED = re.compile(r"\bbigint\s+UNSIGNED\b", re.IGNORECASE)

# AUTO_INCREMENT with bigint
RE_AI_BIGINT = re.compile(
    r"(""?)(\w+)\1\s+bigint\s+NOT\s+NULL\s+AUTO_INCREMENT",
    re.IGNORECASE,
)
# AUTO_INCREMENT with int
RE_AI_INT = re.compile(
    r"(""?)(\w+)\1\s+int\s+NOT\s+NULL\s+AUTO_INCREMENT",
    re.IGNORECASE,
)

# datetime(6)
RE_DATETIME = re.compile(r"\bdatetime\s*\(\s*(\d+)\s*\)", re.IGNORECASE)

# longtext
RE_LONGTEXT = re.compile(r"\blongtext\b", re.IGNORECASE)

# ENUM for bitmap_role column
RE_ENUM_BITMAP = re.compile(
    r"""("bitmap_role"\s+)enum\s*\(\s*'object'\s*,\s*'operate'\s*,\s*'result'\s*\)""",
    re.IGNORECASE,
)

# Inline INDEX definition inside CREATE TABLE
# INDEX `name`(`col`[(len)] ASC[, `col2` ASC]) USING BTREE,
RE_INLINE_INDEX = re.compile(
    r",?\s*INDEX\s+""(\w+)""\s*\((.*?)\)(?:\s*USING\s+BTREE)?\s*(?=,|\n)",
)

# Inline UNIQUE INDEX inside CREATE TABLE
RE_INLINE_UNIQUE = re.compile(
    r",?\s*UNIQUE\s+INDEX\s+""(\w+)""\s*\((.*?)\)(?:\s*USING\s+BTREE)?\s*(?=,|\n)",
)

# Index column prefix length like `col`(191) - PG doesn't support
RE_INDEX_PREFIX = re.compile(r"""(\w+)""\s*\(\s*(\d+)\s*\)""")

# FOREIGN KEY constraint - extract name and definition
RE_FK = re.compile(
    r""",?\s*CONSTRAINT\s+""(\w+)""\s+FOREIGN\s+KEY\s*\(([^)]+)\)\s*"""
    r"""REFERENCES\s+""(\w+)""\s*\(([^)]+)\)\s*"""
    r"""(ON\s+DELETE\s+\w+)?\s*(ON\s+UPDATE\s+\w+)?\s*(?=,|\n)""",
)

# Trigger - MySQL delimiter
RE_DELIMITER = re.compile(r"^delimiter\s+;;", re.IGNORECASE)
RE_SEMICOLON_SEMICOLON = re.compile(r"^;;$")

# Index on prefix like `title`(191)
RE_COL_PREFIX = re.compile(r"""(\w+)""\s*\(\s*(\d+)\s*\)""")


def quote_ident(m):
    """Wrap a captured identifier in double quotes."""
    return '"' + m.group(1) + '"'


def convert_create_table(body, table_name):
    """
    Process a CREATE TABLE statement body (between parentheses).
    Returns (new_body, extra_statements).
    extra_statements are CREATE INDEX / COMMENT ON etc. to emit after the table.
    """
    extra = []

    # 1. Remove inline CHARACTER SET / COLLATE from columns
    body = RE_COL_CHARSET.sub("", body)
    body = RE_COL_COLLATE.sub("", body)

    # 2. Remove USING BTREE
    body = RE_USING_BTREE.sub("", body)

    # 3. Remove ON UPDATE CURRENT_TIMESTAMP
    body = RE_ON_UPDATE.sub("", body)

    # 4. Remove COMMENT
    body = RE_COMMENT.sub("", body)

    # 5. NULL DEFAULT NULL → DEFAULT NULL (ok in PG)
    # body = RE_NULL_DEFAULT_NULL.sub(" DEFAULT NULL", body)

    # 6. Fix data types
    body = RE_INT_UNSIGNED.sub("integer", body)
    body = RE_BIGINT_UNSIGNED.sub("bigint", body)
    body = RE_LONGTEXT.sub("text", body)
    body = RE_DATETIME.sub(r"timestamp(\1) without time zone", body)

    # 7. AUTO_INCREMENT → SERIAL / BIGSERIAL
    # Must do BEFORE extracting indexes because AUTO_INCREMENT columns
    # are typically PRIMARY KEY

    # bigint NOT NULL AUTO_INCREMENT → BIGSERIAL
    body = RE_AI_BIGINT.sub(r'"\2" BIGSERIAL', body)
    # int NOT NULL AUTO_INCREMENT → SERIAL
    body = RE_AI_INT.sub(r'"\2" SERIAL', body)

    # 8. ENUM → varchar + CHECK
    body = RE_ENUM_BITMAP.sub(
        r'\1varchar(20) NOT NULL', body
    )
    if 'bitmap_role' in body and 'varchar(20)' in body:
        extra.append(
            f'ALTER TABLE "{table_name}" ADD CONSTRAINT '
            f'"chk_{table_name}_bitmap_role" CHECK '
            f'("bitmap_role" IN (\'object\', \'operate\', \'result\'));'
        )

    # 9. Extract inline UNIQUE INDEX → convert to UNIQUE constraint
    def convert_unique(m):
        idx_name = m.group(1)
        cols = m.group(2)
        # Fix prefix length on columns
        cols_fixed = RE_INDEX_PREFIX.sub(r'"\1"', cols)
        return f',\n  CONSTRAINT "{idx_name}" UNIQUE ({cols_fixed})'

    body = RE_INLINE_UNIQUE.sub(convert_unique, body)

    # 10. Extract inline INDEX → separate CREATE INDEX
    def extract_index(m):
        idx_name = m.group(1)
        cols = m.group(2)
        cols_fixed = RE_INDEX_PREFIX.sub(r'"\1"', cols)
        extra.append(
            f'CREATE INDEX "{idx_name}" ON "{table_name}" ({cols_fixed});'
        )
        return ""  # Remove from body

    body = RE_INLINE_INDEX.sub(extract_index, body)

    # 11. Fix FOREIGN KEY → keep but clean up backticks (already done)
    # FOREIGN KEY references should still have ON DELETE / ON UPDATE

    # 12. Fix index column prefix on PRIMARY KEY too
    body = RE_INDEX_PREFIX.sub(r'"\1"', body)

    # 13. Clean up: remove double commas
    body = re.sub(r",\s*,", ",", body)
    body = re.sub(r",\s*\)", "\n)", body)
    body = re.sub(r"\(\s*,", "(", body)

    return body, extra


def convert_trigger(lines_iter, output_lines):
    """
    Convert MySQL trigger to PostgreSQL PL/pgSQL trigger + function.
    """
    # We need to find the full trigger definition
    trigger_sql = []
    in_trigger = False
    for line in lines_iter:
        if line.strip().startswith("CREATE TRIGGER"):
            in_trigger = True
        if in_trigger:
            trigger_sql.append(line)
            if line.strip() == ";;":
                break

    if not trigger_sql:
        return

    full_text = " ".join(trigger_sql)
    # Parse: CREATE TRIGGER "name" BEFORE UPDATE ON "table" FOR EACH ROW SET ...
    m = re.match(
        r'CREATE\s+TRIGGER\s+"(\w+)"\s+'
        r'(BEFORE|AFTER)\s+(UPDATE|INSERT|DELETE)\s+'
        r'ON\s+"(\w+)"\s+'
        r'FOR\s+EACH\s+ROW\s+'
        r'SET\s+(.*?)\s*;;',
        full_text,
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        trig_name = m.group(1)
        timing = m.group(2)
        event = m.group(3)
        table = m.group(4)
        body = m.group(5).strip()

        # Convert body: NEW.col = (subquery)  →  NEW.col := (subquery);
        # Also wrap in IF condition if needed
        func_name = f"{trig_name}_fn"

        output_lines.append(f"\n-- Converted trigger: {trig_name}")
        output_lines.append(
            f"CREATE OR REPLACE FUNCTION \"{func_name}\"() "
            f"RETURNS trigger AS $$\n"
            f"BEGIN\n"
            f"  {body};\n"
            f"  RETURN NEW;\n"
            f"END;\n"
            f"$$ LANGUAGE plpgsql;\n"
        )
        output_lines.append(
            f'CREATE TRIGGER "{trig_name}" '
            f"{timing} {event} ON \"{table}\" "
            f"FOR EACH ROW EXECUTE FUNCTION \"{func_name}\"();\n"
        )


def process_file(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    output_lines = []
    i = 0
    total = len(lines)

    # Track CREATE TABLE state
    in_create_table = False
    create_table_name = ""
    create_body_lines = []
    create_header = ""

    while i < total:
        line = lines[i]

        # ── Handle SET NAMES ──
        if line.strip().startswith("SET NAMES"):
            output_lines.append(
                "-- SET NAMES utf8mb4; -- not needed in PostgreSQL\n"
            )
            i += 1
            continue

        # ── Handle SET FOREIGN_KEY_CHECKS ──
        if line.strip() == "SET FOREIGN_KEY_CHECKS = 0;":
            output_lines.append(
                "SET session_replication_role = 'replica';\n"
            )
            i += 1
            continue
        if line.strip() == "SET FOREIGN_KEY_CHECKS = 1;":
            output_lines.append(
                "SET session_replication_role = 'origin';\n"
            )
            i += 1
            continue

        # ── Handle delimiter ──
        if RE_DELIMITER.match(line.strip()):
            # Look ahead for trigger
            convert_trigger(iter(lines[i + 1 :]), output_lines)
            # Skip the rest of the trigger and delimiter
            while i < total:
                if lines[i].strip() == "delimiter ;":
                    i += 1
                    break
                i += 1
            continue

        # ── Handle DROP TABLE IF EXISTS ──
        if line.strip().startswith("DROP TABLE IF EXISTS"):
            # Replace backticks with double quotes
            cleaned = line.replace("`", '"')
            output_lines.append(cleaned)
            i += 1
            continue

        # ── Handle CREATE TABLE ──
        if line.strip().startswith("CREATE TABLE"):
            in_create_table = True
            create_body_lines = []
            # Extract table name
            m = re.search(r'CREATE\s+TABLE\s+"(\w+)"', line.replace("`", '"'))
            if m:
                create_table_name = m.group(1)
            create_header = line.replace("`", '"')
            i += 1
            continue

        if in_create_table:
            # Check if this line ends the CREATE TABLE
            if re.search(
                r"\)\s*ENGINE\s*=", line, re.IGNORECASE
            ) or (
                line.strip().endswith(";")
                and "ENGINE" not in line
                and not line.strip().startswith(")")
                and len(create_body_lines) > 5
            ):
                # End of CREATE TABLE body
                # The closing ) and ENGINE clause may span lines
                # Collect remaining lines of the definition
                create_body_lines.append(line)
                full_body = "".join(create_body_lines)
                in_create_table = False

                # Remove ENGINE, AUTO_INCREMENT, CHARACTER SET, COLLATE, ROW_FORMAT
                full_body = RE_TABLE_ENGINE.sub(");", full_body)

                # Replace backticks
                full_body = full_body.replace("`", '"')

                # Process
                new_body, extra_stmts = convert_create_table(
                    full_body, create_table_name
                )

                output_lines.append(create_header.rstrip())
                output_lines.append(new_body)
                output_lines.append("\n")
                for stmt in extra_stmts:
                    output_lines.append(stmt + "\n")
                output_lines.append("\n")

                create_table_name = ""
                create_body_lines = []
                create_header = ""
                i += 1
                continue
            else:
                create_body_lines.append(line)
                i += 1
                continue

        # ── Handle INSERT statements ──
        # Just replace backticks around table names
        cleaned = line.replace("`", '"')
        output_lines.append(cleaned)
        i += 1

    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(output_lines)

    print(f"Conversion complete: {input_path} → {output_path}")
    print(f"Total lines: {total}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_mysql_to_pg.py <input.sql> [output.sql]")
        sys.exit(1)

    input_path = sys.argv[1]
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_pg{ext}"

    process_file(input_path, output_path)


if __name__ == "__main__":
    main()
