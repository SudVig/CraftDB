"""
run_semantic_check.py — runs the SemanticAnalyzer against a real AST list
"""

import json
from StorageEngine import StorageEngine
from SemanticAnalyzer import SemanticAnalyzer

ast_list = [
    {'type': 'insert', 'table': 'users', 'columns': ['id', 'name', 'age'], 'values': [['1', 'John', '30']]},
    {'type': 'insert', 'table': 'users', 'columns': ['id', 'name', 'age'], 'values': [['2', 'Jane', '25'], ['3', 'Bob', '40']]},
    {'type': 'insert', 'table': 'users', 'columns': [], 'values': [['2', 'Jane', '25'], ['3', 'Bob', '40']]},
    {'type': 'database', 'action': 'create', 'name': 'mydb'},
    {'type': 'database', 'action': 'use', 'name': 'mydb'},
    {'type': 'database', 'action': 'show'},
    {'type': 'database', 'action': 'drop', 'name': 'mydb'},
    {'type': 'table', 'action': 'create', 'name': 'users', 'columns': [
        {'name': 'id', 'datatype': 'int'}, {'name': 'name', 'datatype': 'string'}, {'name': 'age', 'datatype': 'int'}
    ], 'primary_key': 'id'},
    {'type': 'table', 'action': 'create', 'name': 'users', 'columns': [
        {'name': 'id', 'datatype': 'int'}, {'name': 'name', 'datatype': 'string'},
        {'name': 'age', 'datatype': 'int'}, {'name': 'temp', 'datatype': 'float'}
    ], 'primary_key': None},
    {'type': 'table', 'action': 'drop', 'name': 'mydb'},
    {'type': 'table', 'action': 'show'},
    {'type': 'table', 'action': 'describe', 'name': 'users'},
    {'type': 'table', 'action': 'rename', 'old_name': 'mydb', 'new_name': 'users'},
    {'type': 'select', 'action': 'query', 'table': 'users', 'columns': ['*'],
     'where': [{'left': 'age', 'operator': '>', 'right': 30}],
     'order_by': {'column': 'name', 'direction': 'ASC'}, 'limit': 10},
    {'type': 'select', 'action': 'query', 'table': 'users', 'columns': ['age'],
     'where': [{'left': 'age', 'operator': '<', 'right': 30}],
     'order_by': {'column': 'name', 'direction': 'DESC'}, 'limit': 5},
    {'type': 'select', 'action': 'query', 'table': 'users', 'columns': ['name', 'age'],
     'where': [{'left': 'age', 'operator': '>=', 'right': 18}, 'AND', {'left': 'age', 'operator': '<=', 'right': 65}],
     'order_by': {'column': 'name', 'direction': 'ASC'}, 'limit': 20},
    {'type': 'select', 'action': 'query', 'table': 'users', 'columns': ['name', 'age'],
     'where': [{'left': 'age', 'operator': '>=', 'right': 18}, 'OR', {'left': 'age', 'operator': '<=', 'right': 65}],
     'order_by': {'column': 'name', 'direction': 'DESC'}, 'limit': 15},
    {'type': 'select', 'action': 'query', 'table': 'users', 'columns': ['name', 'age'],
     'where': [{'left': 'age', 'operator': '!=', 'right': 30}],
     'order_by': {'column': 'name', 'direction': 'ASC'}, 'limit': 10},
    {'type': 'select', 'action': 'query', 'table': 'users', 'columns': ['name', 'age'],
     'where': [{'left': 'age', 'operator': '=', 'right': 30}],
     'order_by': {'column': 'name', 'direction': 'DESC'}, 'limit': 5},
    {'type': 'update', 'action': 'update', 'table': 'users', 'set': [{'column': 'age', 'value': 31}],
     'where': [{'left': 'id', 'operator': '=', 'right': 1}]},
    {'type': 'update', 'action': 'update', 'table': 'users', 'set': [{'column': 'name', 'value': 'John Doe'}],
     'where': [{'left': 'id', 'operator': '=', 'right': 1}]},
    {'type': 'update', 'action': 'update', 'table': 'users',
     'set': [{'column': 'age', 'value': 32}, {'column': 'name', 'value': 'John Smith'}],
     'where': [{'left': 'id', 'operator': '=', 'right': 1}]},
    {'type': 'update', 'action': 'update', 'table': 'users',
     'set': [{'column': 'qty', 'value': 33.12}, {'column': 'name', 'value': 'John Doe'}],
     'where': [{'left': 'id', 'operator': '=', 'right': 1}, 'AND', {'left': 'name', 'operator': '=', 'right': 'John Smith'}]},
    {'type': 'update', 'action': 'update', 'table': 'users', 'set': [{'column': 'age', 'value': 34}],
     'where': [{'left': 'id', 'operator': '=', 'right': 1}, 'OR', {'left': 'name', 'operator': '=', 'right': 'John Doe'}]},
    {'type': 'update', 'action': 'update', 'table': 'users', 'set': [{'column': 'age', 'value': 35}],
     'where': [{'left': 'id', 'operator': '=', 'right': 1}, 'AND', {'left': 'name', 'operator': '=', 'right': 'John Doe'},
               'OR', {'left': 'age', 'operator': '=', 'right': 30}]},
    {'type': 'delete', 'action': 'delete', 'table': 'users', 'where': [{'left': 'id', 'operator': '=', 'right': 1}]},
    {'type': 'delete', 'action': 'delete', 'table': 'users', 'where': [{'left': 'name', 'operator': '=', 'right': 'John Doe'}]},
    {'type': 'delete', 'action': 'delete', 'table': 'users', 'where': [{'left': 'age', 'operator': '>', 'right': 30}]},
    {'type': 'delete', 'action': 'delete', 'table': 'users',
     'where': [{'left': 'age', 'operator': '<', 'right': 30}, 'AND', {'left': 'name', 'operator': '=', 'right': 'Jane Doe'}]},
    {'type': 'delete', 'action': 'delete', 'table': 'users',
     'where': [{'left': 'age', 'operator': '>=', 'right': 18}, 'OR', {'left': 'age', 'operator': '<=', 'right': 65}]},
]

if __name__ == "__main__":
    print("Before SE")
    storage = StorageEngine()
    print("After SE")
    analyzer = SemanticAnalyzer(storage)
    report = analyzer.analyze(ast_list)

    ok_count = sum(1 for r in report if r["status"] == "OK")
    error_count = len(report) - ok_count

    for r in report:
        if r["status"] == "OK":
            print(f"[{r['index']:>2}] OK     {r['statement'].get('type')} / {r['statement'].get('action')}")
        else:
            print(f"[{r['index']:>2}] ERROR  {r['statement'].get('type')} / {r['statement'].get('action')} -> {r['message']}")

    print("\n" + "=" * 60)
    print(f"{ok_count} statement(s) passed, {error_count} statement(s) failed semantic checks.")