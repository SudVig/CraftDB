"""
CraftDB web backend
--------------------
Tiny Flask server that serves index.html and exposes two JSON endpoints
so the web UI can talk to your existing CraftDB pipeline:

    GET  /api/schema    -> { databases: {dbName: {tableName: {columns, primary_key}}}, current: name }
    POST /api/execute   -> { query: "..." }  =>  { ok: true, result: [...] }
                                              or  { ok: false, error: "..." }

Run it with:
    pip install flask flask-cors
    python server.py
Then open http://127.0.0.1:5000 in a browser.

Place this file in the SAME folder as your existing `main.py` (it reuses
the exact same import setup).
"""

import os
import sys
import traceback

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# ---------------------------------------------------------------------------
# Same import setup as main.py: CraftDB/ lives one level up from this file.
# ---------------------------------------------------------------------------
_PARENT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PARENT_FOLDER not in sys.path:
    sys.path.append(_PARENT_FOLDER)

from Craftql.lexer import tokenize
from Craftql.parser import parser
from CraftDB.StorageEngine import StorageEngine
from CraftDB.SemanticAnalyzer import SemanticAnalyzer
from CraftDB.Executor import Executor


# ---------------------------------------------------------------------------
# Schema introspection — uses StorageEngine's actual public API
# (list_databases, list_tables, get_table_schema, get_current_database)
# instead of guessing at internal attribute names.
# ---------------------------------------------------------------------------
def get_schema_info(storage):
    """
    Returns:
        {
          "mydb": {
            "users": {
              "columns": {"id": "int", "name": "string", "score": "int"},
              "primary_key": "id"
            },
            ...
          },
          ...
        }
    """
    info = {}
    try:
        db_names = storage.list_databases()
    except Exception:
        return info

    for db_name in db_names:
        info[str(db_name)] = {}
        try:
            table_names = storage.list_tables(db_name)
        except Exception:
            table_names = []

        for table_name in table_names:
            try:
                schema = storage.get_table_schema(db_name, table_name)
                info[str(db_name)][str(table_name)] = {
                    "columns": schema.get("columns", {}),
                    "primary_key": schema.get("primary_key"),
                }
            except Exception:
                info[str(db_name)][str(table_name)] = {"columns": {}, "primary_key": None}
    return info


def get_current_database(storage):
    try:
        current = storage.get_current_database()
        return str(current) if current else None
    except Exception:
        return None


app = Flask(__name__, static_folder=None)
# Allows the API to be called from a different origin (e.g. a Live Server
# tab on :5500) instead of only from pages Flask itself serves on :5000.
# If the HTML is always served by this same Flask app, this isn't required.
CORS(app, resources={r"/api/*": {"origins": "*"}})

# One long-lived session for the whole server process, so
# `craft database use X;` persists between requests — same idea as a
# real DB client holding one open connection.
storage = StorageEngine()
analyzer = SemanticAnalyzer(storage)
executor = Executor()


@app.route("/")
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "index.html")


@app.route("/api/schema")
def schema():
    try:
        databases = get_schema_info(storage)
    except Exception:
        databases = {}
    try:
        current = get_current_database(storage)
    except Exception:
        current = None
    return jsonify({"databases": databases, "current": current})


@app.route("/api/execute", methods=["POST"])
def execute():
    body = request.get_json(silent=True) or {}
    query_text = (body.get("query") or "").strip()
    if not query_text:
        return jsonify({"ok": False, "error": "Empty query"}), 400

    try:
        tokens = tokenize(query_text)
        ast = parser(tokens)
        queries = analyzer.analyze(ast)

        results = []
        for q in queries:
            if q.get("status") != "OK":
                raise Exception(f"Invalid Query: {q}")
            out = executor.execute_query(q["statement"])
            results.append(out)
        print(results)
        # Printed as-is, same as main.py's print(result).
        result = jsonify({"ok": True, "result": results})
        
        return result
    except Exception as e:
        return jsonify({"ok": False, "error": f"{e}\n\n{traceback.format_exc()}"}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)

# [{'result_type': 'list', 'result': ['TEMP']}]