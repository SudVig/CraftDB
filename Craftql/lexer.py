"""
simple_lexer.py — A SIMPLE tokenizer for CraftQL
"""

# ---------------------------------------------------------
# 1. List of reserved words CraftQL understands
# ---------------------------------------------------------
KEYWORDS = [
    "craft", "database", "use", "table", "tables",
    "insert", "into", "values",
    "select", "from",
    "update", "set",
    "delete",
    "alter", "drop", "rename", "describe",
    "show", "count", "where", "order", "by",
    "asc", "desc", "limit",
    "primary", "to", "add",
    "and", "or", "not",
    "true", "false",
    "int", "float","string"
]

# ---------------------------------------------------------
# 2. Symbols that are exactly one character
# ---------------------------------------------------------
SYMBOLS = {
    "{": "LBRACE",
    "}": "RBRACE",
    "(": "LPAREN",
    ")": "RPAREN",
    "[": "LBRACKET",
    "]": "RBRACKET",
    ":": "COLON",
    ",": "COMMA",
    ";": "SEMICOLON",
    ".": "DOT",
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "%": "PERCENT",
    "=": "ASSIGN",
    ">": "GREATER",
    "<": "LESS",
}


def tokenize(query_string):

    tokens = []
    length = len(query_string)
    i = 0
    new_line = 1

    while i < length:

        ch = query_string[i]

        # -------------------------------------------------
        # White spaces
        # -------------------------------------------------
        if ch in " \t\n\r":
            if ch == "\n":
                new_line += 1
            i += 1
            continue

        # -------------------------------------------------
        # Single line comments
        # -------------------------------------------------
        if ch == "#":
            while i < length and query_string[i] != "\n":
                i += 1
            continue

        # -------------------------------------------------
        # Multi line comments
        # -------------------------------------------------
        if ch == "/" and i + 1 < length and query_string[i + 1] == "*":

            i += 2

            while i < length and not (
                query_string[i] == "*" and
                i + 1 < length and
                query_string[i + 1] == "/"
            ):

                if query_string[i] == "\n":
                    new_line += 1

                i += 1

            if i >= length:
                raise ValueError("Unterminated multiline comment")

            i += 2
            continue

        # -------------------------------------------------
        # Strings
        # -------------------------------------------------
        if ch == '"' or ch == "'":

            quote_type = ch
            i += 1
            start = i

            while i < length and query_string[i] != quote_type:
                i += 1

            if i >= length:
                raise ValueError("Unterminated string literal")

            value = query_string[start:i]

            i += 1

            tokens.append({
                "type": "STRING",
                "value": value,
                "line": new_line,
                "column": start + 1
            })

            continue

        # -------------------------------------------------
        # Numbers
        # -------------------------------------------------
        if ch.isdigit():

            start = i

            while i < length and query_string[i].isdigit():
                i += 1

            if i < length and query_string[i] == ".":

                i += 1

                while i < length and query_string[i].isdigit():
                    i += 1

                value = query_string[start:i]

                tokens.append({
                    "type": "FLOAT",
                    "value": float(value),
                    "line": new_line,
                    "column": start + 1
                })

            else:

                value = query_string[start:i]

                tokens.append({
                    "type": "INTEGER",
                    "value": int(value),
                    "line": new_line,
                    "column": start + 1
                })

            continue

        # -------------------------------------------------
        # Identifiers / Keywords
        # -------------------------------------------------
        if ch.isalpha() or ch == "_":

            start = i

            while i < length and (
                query_string[i].isalnum() or query_string[i] == "_"
            ):
                i += 1

            value = query_string[start:i]

            if value.lower() in KEYWORDS:

                tokens.append({
                    "type": "KEYWORD",
                    "value": value.lower(),
                    "line": new_line,
                    "column": start + 1
                })

            else:

                tokens.append({
                    "type": "IDENTIFIER",
                    "value": value,
                    "line": new_line,
                    "column": start + 1
                })

            continue

        # -------------------------------------------------
        # Two-character symbols
        # -------------------------------------------------

        if ch == "=" and i + 1 < length and query_string[i + 1] == "=":
            tokens.append({
                "type": "EQ",
                "value": "==",
                "line": new_line,
                "column": i + 1
            })
            i += 2
            continue

        if ch == ">" and i + 1 < length and query_string[i + 1] == "=":
            tokens.append({
                "type": "GTE",
                "value": ">=",
                "line": new_line,
                "column": i + 1
            })
            i += 2
            continue

        if ch == "<" and i + 1 < length and query_string[i + 1] == "=":
            tokens.append({
                "type": "LTE",
                "value": "<=",
                "line": new_line,
                "column": i + 1
            })
            i += 2
            continue

        if ch == "!" and i + 1 < length and query_string[i + 1] == "=":
            tokens.append({
                "type": "NEQ",
                "value": "!=",
                "line": new_line,
                "column": i + 1
            })
            i += 2
            continue

        # -------------------------------------------------
        # Single-character symbols
        # -------------------------------------------------
        if ch in SYMBOLS:

            tokens.append({
                "type": SYMBOLS[ch],
                "value": ch,
                "line": new_line,
                "column": i + 1
            })

            i += 1
            continue

        raise ValueError(
            f"Unexpected character: {ch} at row {new_line} column {i+1}"
        )

    tokens.append({
        "type": "EOF",
        "value": None,
        "line": new_line,
        "column": i + 1
    })
    
    return tokens