# CraftQL 🛠️

**CraftQL** is a custom relational database engine and query language, built from scratch in Python. It implements its own lexer, parser, and execution engine to support a SQL-like syntax for defining databases, tables, and performing CRUD operations — with all data held **in memory** and rows indexed using a **binary search tree** on the primary key.

---

## ✨ Features

- Custom query language with its own grammar (`craft ...;`)
- Full CRUD support: `insert`, `select`, `update`, `delete`
- In-memory relational storage — no files, no external database
- Binary search tree indexing on the primary key for fast lookups
- Schema management: create/alter/drop tables and databases
- Filtering with `where`, sorting with `order by`, and `limit`
- Single-line (`#`, `//`) and multi-line (`/* */`) comments
- Lightweight, dependency-free — pure Python, no external database

---

## 🏗️ Architecture

CraftQL follows a classic language-processing pipeline:

```
Raw Query String
       │
       ▼
┌───────────────┐
│    Lexer      │   Tokenizes text into keywords, identifiers,
│ (lexer.py)    │   operators, literals
└──────┬────────┘
       ▼
┌───────────────┐
│    Parser     │   Converts tokens into an Abstract Syntax
│ (parser.py)   │   Tree (AST) based on CraftQL grammar
└──────┬────────┘
       ▼
┌───────────────┐
│  AST Nodes    │   SelectNode, InsertNode, UpdateNode,
│(ast_nodes.py) │   DeleteNode, CreateTableNode, etc.
└──────┬────────┘
       ▼
┌───────────────┐
│   Executor    │   Walks the AST, applies operations
│ (executor.py) │   against in-memory tables
└──────┬────────┘
       ▼
┌───────────────┐
│  Table Store  │   Rows held in memory, one Binary
│ (storage.py)  │   Search Tree per table (keyed on
└───────────────┘   the primary key) for fast lookups
```

### Project Structure

```
craftql/
├── lexer.py         # Tokenizer
├── parser.py         # Token stream → AST
├── ast_nodes.py       # AST node definitions
├── executor.py         # AST execution against in-memory tables
├── bst.py               # Binary Search Tree used for primary-key indexing
├── storage.py             # In-memory table/database management
├── engine.py               # Public entry point: CraftQL().run(query)
├── cli.py                   # Interactive REPL shell
└── tests/
    └── test_engine.py
```

### Data Model

Each table is held **in memory** as a Python object with:
- a **schema** (column name → data type mapping)
- a **primary key** column
- a **Binary Search Tree** that indexes rows by their primary key, giving fast insert/lookup/delete instead of scanning a list

```python
class Table:
    def __init__(self, name, schema, primary_key):
        self.name = name
        self.schema = schema          # {"id": "int", "name": "text", "age": "int"}
        self.primary_key = primary_key
        self.index = BinarySearchTree()   # keyed on primary_key value

class BSTNode:
    def __init__(self, key, row):
        self.key = key        # primary key value
        self.row = row         # dict of the full row, e.g. {"id": 1, "name": "Alice"}
        self.left = None
        self.right = None

class BinarySearchTree:
    def insert(self, key, row):
        ...   # standard BST insert, ordered by key

    def find(self, key):
        ...   # O(log n) average lookup by primary key

    def delete(self, key):
        ...   # standard BST delete with successor/predecessor handling

    def in_order(self):
        ...   # in-order traversal → naturally sorted rows by primary key
```

**Why a BST here:**
- `select ... where id == <value>` → BST lookup instead of a full scan
- `select ... order by <primary_key>` → in-order traversal returns rows already sorted
- `delete ... where id == <value>` → BST delete keeps the tree balanced-ish without rebuilding from scratch

Since everything lives in memory, **restarting the process clears all data** — there's no persistence layer yet (see Roadmap).

---

## 🚀 Getting Started

```bash
git clone https://github.com/sudvig/craftql.git
cd craftql
python -m craftql.cli
```

```
craft> craft database school;
craft> craft use school;
craft> craft table students(
    id:int,
    name:text,
    age:int,
    primary(id)
);
craft> craft insert students{ id:1, name:"Alice", age:22 };
craft> craft select students where age > 18;
```

---

## 📖 CraftQL v1.0 Syntax Reference

### DATABASE
```
craft database <database_name>;
craft use <database_name>;
craft show databases;
craft drop database <database_name>;
```

### TABLE
```
craft table <table_name>(
    <column>:<datatype>,
    ...
    primary(<column>)
);
craft show tables;
craft describe <table_name>;
craft drop table <table_name>;
```

### INSERT

**Single row:**
```
craft insert <table_name>{
    <column>:<value>,
    ...
};
```

**Multiple rows (bulk insert):**
```
craft insert <table_name>[
{
    ...
},
{
    ...
}
];
```

### SELECT

**All columns:**
```
craft select <table_name>;
```

**Specific columns:**
```
craft select <table_name>{
    column1,
    column2,
    ...
};
```

**With a filter:**
```
craft select <table_name>{
    ...
}
where <condition>;
```

**With a filter, sorted ascending:**
```
craft select <table_name>{
    ...
}
where <condition>
order by <column> asc;
```

**With a filter, sorted descending:**
```
craft select <table_name>{
    ...
}
where <condition>
order by <column> desc;
```

**Limit the number of rows returned:**
```
craft select <table_name>
limit <number>;
```

### UPDATE
```
craft update <table_name>{
    column:value
}
where <condition>;

craft update <table_name>{
    column1:value,
    column2:value
}
where <condition>;
```

### DELETE
```
craft delete <table_name>;

craft delete <table_name>
where <condition>;
```

### ALTER TABLE
```
craft alter <table_name>
add <column>:<datatype>;

craft alter <table_name>
drop <column>;

craft alter <table_name>
rename <old_column>
to <new_column>;
```

### RENAME TABLE
```
craft rename table <old_name>
to <new_name>;
```

### COUNT
```
craft count <table_name>;

craft count <table_name>
where <condition>;
```

---

## ⚙️ Operators

**Arithmetic**
```
+   -   *   /   %
```

**Comparison**
```
==   !=   >   <   >=   <=
```

**Logical**
```
and   or   not
```

---

## 🗃️ Data Types

```
int
float
text
bool
```

---

## 🔑 Keywords

```
craft, database, use, table, insert, select, update, delete,
alter, drop, rename, describe, show, count, where, order, by,
limit, primary, to, add, and, or, not, true, false
```

---

## 💬 Comments

```
# Single line
// Single line
/*
 Multi-line
*/
```

---

## Statement Terminator

Every statement ends with `;`

---

## 🧪 Basic CRUD — Syntax, Example & Output

Setup used for every example below:

```
craft database library;
craft use library;

craft table books(
    id:int,
    title:text,
    available:bool,
    primary(id)
);
```

### CREATE (Insert)

**Syntax:**
```
craft insert <table_name>{
    <column>:<value>,
    ...
};
```

**Example:**
```
craft insert books{ id:1, title:"Clean Code", available:true };
craft insert books{ id:2, title:"The Pragmatic Programmer", available:false };
```

**Output:**
```
2 row(s) inserted into 'books'.
```

---

### READ (Select)

**Syntax:**
```
craft select <table_name>
where <condition>;
```

**Example:**
```
craft select books
where available == true;
```

**Output:**
```
+----+--------------+------------+
| id | title        | available  |
+----+--------------+------------+
| 1  | Clean Code   | true       |
+----+--------------+------------+
1 row(s) returned.
```

---

### UPDATE

**Syntax:**
```
craft update <table_name>{
    column:value
}
where <condition>;
```

**Example:**
```
craft update books{ available:true }
where id == 2;
```

**Output:**
```
1 row(s) updated in 'books'.
```

Verify with a read:
```
craft select books;
```
```
+----+------------------------------+------------+
| id | title                        | available  |
+----+------------------------------+------------+
| 1  | Clean Code                   | true       |
| 2  | The Pragmatic Programmer     | true       |
+----+------------------------------+------------+
2 row(s) returned.
```

---

### DELETE

**Syntax:**
```
craft delete <table_name>
where <condition>;
```

**Example:**
```
craft delete books
where id == 1;
```

**Output:**
```
1 row(s) deleted from 'books'.
```

Verify with a read:
```
craft select books;
```
```
+----+------------------------------+------------+
| id | title                        | available  |
+----+------------------------------+------------+
| 2  | The Pragmatic Programmer     | true       |
+----+------------------------------+------------+
1 row(s) returned.
```

---

## 🗺️ Roadmap

- [ ] Persistence (save/load in-memory tables to disk)
- [ ] Joins across tables
- [ ] Aggregate functions (`sum`, `avg`, `min`, `max`)
- [ ] Balanced tree (AVL/Red-Black) to avoid BST worst-case skew
- [ ] Transaction support
- [ ] Export/import (CSV, SQL dump)

---

## 📄 License

MIT
