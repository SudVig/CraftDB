"""
Simplified disk-based storage engine (CraftQL)
------------------------------------------------
Concepts kept from your original design:
- Header page: page_number, version, row_size, key_page_offset, data_page_start
- Data page: rows packed with struct, fixed row size
- Key page: (key -> offset) lookup, kept as a dict + JSON sidecar for now
  (this is the piece to later split into real 4096-byte paged blocks)

Supported operations:
- insert(row)
- search_by_key(key)
- search_where(column, value)
- update_by_key(key, updates)
- update_where(column, value, updates)
"""

import os
import json
import struct


class BPlusTree:

    TYPE_MAP = {"int": "i", "float": "f", "ulong": "Q"}
    STRING_SIZE = 255

    def __init__(self, table_name, schema, primary_key, db_path="./DB"):
        """
        schema example:
            {"id": "int", "name": "string", "score": "int"}
        primary_key example:
            "id"
        """
        self.table = table_name
        self.schema = schema
        self.primary_key = primary_key

        os.makedirs(db_path, exist_ok=True)
        self.file_path = os.path.join(db_path, f"{table_name}.cdb")

        self.row_format, self.row_size = self._build_format(schema)

        # ---- header ----
        self.HEADER_FMT = "<iiiiQ"   # page_number, version, row_size, key_page_offset, data_page_start
        self.HEADER_SIZE = struct.calcsize(self.HEADER_FMT)

        self._init_file()

    # ---------------- setup ----------------

    def _build_format(self, schema):
        fmt = "<"
        for col, typ in schema.items():
            fmt += "255s" if typ == "string" else self.TYPE_MAP[typ]
        return fmt, struct.calcsize(fmt)

    def _init_file(self):
        # FileIOEngine.create_table_file may have already touched this path
        # into existence as a 0-byte file. Check size, not just existence,
        # so the header still gets written in that case.
        file_is_ready = (
            os.path.exists(self.file_path)
            and os.path.getsize(self.file_path) >= self.HEADER_SIZE
        )

        if not file_is_ready:
            with open(self.file_path, "wb") as f:
                f.write(struct.pack(
                    self.HEADER_FMT,
                    0,                  # page_number
                    1,                  # version
                    self.row_size,      # row_size
                    self.HEADER_SIZE,   # key_page_offset (placeholder for now)
                    self.HEADER_SIZE    # data_page_start
                ))
            self.key_index = {}
            self._save_index()
        else:
            self._load_index()

    def _index_path(self):
        return self.file_path + ".index.json"

    def _load_index(self):
        path = self._index_path()
        if os.path.exists(path):
            with open(path) as f:
                self.key_index = json.load(f)
        else:
            self.key_index = {}

    def _save_index(self):
        with open(self._index_path(), "w") as f:
            json.dump(self.key_index, f)

    # ---------------- row pack/unpack ----------------

    def _pack_row(self, row):
        values = []
        for col, typ in self.schema.items():
            val = row.get(col)
            if typ == "string":
                values.append(str(val).encode("utf-8")[:255].ljust(255, b"\0"))
            else:
                values.append(val)
        return struct.pack(self.row_format, *values)

    def _unpack_row(self, data):
        values = struct.unpack(self.row_format, data)
        row = {}
        for (col, typ), val in zip(self.schema.items(), values):
            row[col] = val.rstrip(b"\0").decode("utf-8") if typ == "string" else val
        return row

    # ---------------- CRUD ----------------

    def insert(self, row):
        
        key = row[self.primary_key]
        if str(key) in self.key_index:
            raise ValueError(f"Duplicate key {key}")

        with open(self.file_path, "r+b") as f:
            f.seek(0, os.SEEK_END)
            offset = f.tell()
            f.write(self._pack_row(row))

        self.key_index[str(key)] = offset
        self._save_index()
        return offset

    def search_by_key(self, key):
        offset = self.key_index.get(str(key))
        if offset is None:
            return None
        with open(self.file_path, "rb") as f:
            f.seek(offset)
            data = f.read(self.row_size)
        return self._unpack_row(data)

    OPS = {
        "=":  lambda a, b: a == b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        ">":  lambda a, b: a > b,
        "<":  lambda a, b: a < b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
    }

    def _eval_condition(self, cond, row):
        left = row.get(cond["left"])
        right = cond["right"]
        op = cond["operator"]
        return self.OPS[op](left, right)

    def _row_matches(self, row, where):
        """
        where example:
        [{"left": "age", "operator": ">=", "right": 18},
         "AND",
         {"left": "age", "operator": "<=", "right": 65}]

        AND binds tighter than OR (same as SQL), so the list is
        first split into OR-groups, and each group must be fully
        true (all its conditions AND-ed together) for a match.
        """
        if not where:
            return True

        groups = [[]]
        for item in where:
            if item == "OR":
                groups.append([])
            elif item == "AND":
                continue
            else:
                groups[-1].append(item)

        return any(
            all(self._eval_condition(cond, row) for cond in group)
            for group in groups
        )

    def search_where(self, condition):
        results = []
        with open(self.file_path, "rb") as f:
            f.seek(self.HEADER_SIZE)
            while True:
                data = f.read(self.row_size)
                if len(data) < self.row_size:
                    break
                row = self._unpack_row(data)
                if self._row_matches(row, condition):
                    results.append(row)
        return results
    def search_where(self, condition):
        results = []
        with open(self.file_path, "rb") as f:
            f.seek(self.HEADER_SIZE)
            while True:
                data = f.read(self.row_size)
                if len(data) < self.row_size:
                    break
                row = self._unpack_row(data)
                if self._row_matches(row, condition):
                    results.append(row)
        return results
    
    def select(self, columns=None, where=None, order_by=None, limit=None):
        """
        columns: None or ["*"]  -> full rows
                ["id", "name"] -> only these columns
        where: same format as search_where
        order_by: {"column": "age", "direction": "ASC"} or None
        limit: int or None
        """
        rows = self.search_where(where or [])

        if order_by:
            rows.sort(
                key=lambda r: r[order_by["column"]],
                reverse=(order_by["direction"] == "DESC")
            )

        if limit is not None:
            rows = rows[:limit]

        if not columns or columns == ["*"]:
            return rows

        return [
            {col: row[col] for col in columns if col in row}
            for row in rows
        ]
    def update_by_key(self, key, updates):
        offset = self.key_index.get(str(key))
        if offset is None:
            return False
        row = self.search_by_key(key)
        row.update(updates)
        with open(self.file_path, "r+b") as f:
            f.seek(offset)
            f.write(self._pack_row(row))
        return True

    def update_where(self, condition, updates):
        count = 0
        offset = self.HEADER_SIZE
        with open(self.file_path, "r+b") as f:
            while True:
                f.seek(offset)
                data = f.read(self.row_size)
                if len(data) < self.row_size:
                    break
                row = self._unpack_row(data)
                if self._row_matches(row, condition):
                    row.update(updates)
                    f.seek(offset)
                    f.write(self._pack_row(row))
                    count += 1
                offset += self.row_size
        return count
    def update(self, updates, key=None, where=None):
        if key is not None:
            row = self.search_by_key(key)
            if row is None:
                return 0
            if where and not self._row_matches(row, where):
                return 0
            offset = self.key_index[str(key)]
            row.update(updates)
            with open(self.file_path, "r+b") as f:
                f.seek(offset)
                f.write(self._pack_row(row))
            return 1

        count = 0
        offset = self.HEADER_SIZE
        with open(self.file_path, "r+b") as f:
            while True:
                f.seek(offset)
                data = f.read(self.row_size)
                if len(data) < self.row_size:
                    break
                row = self._unpack_row(data)
                if self._row_matches(row, where or []):
                    row.update(updates)
                    f.seek(offset)
                    f.write(self._pack_row(row))
                    count += 1
                offset += self.row_size
        return count
    def delete(self, key=None, where=None):
        """
        key:   primary key value — if given, restricts to that one row
        where: condition list (same format as search_where)

        If both key and where are given, the row must match BOTH:
        it must be the row for `key` AND satisfy `where`.
        If both are omitted, deletes every row in the table.
        Returns the number of rows deleted.
        """
        if key is not None:
            row = self.search_by_key(key)
            if row is None:
                return 0
            if where and not self._row_matches(row, where):
                return 0
            return 1 if self._delete_at_key(key) else 0

        matches = self.search_where(where or [])
        count = 0
        for row in matches:
            if self._delete_at_key(row[self.primary_key]):
                count += 1
        return count
    def _delete_at_key(self, key):
        """Internal: removes the row for `key` via swap-with-last-row + truncate."""
        offset = self.key_index.get(str(key))
        if offset is None:
            return False

        with open(self.file_path, "r+b") as f:
            f.seek(0, os.SEEK_END)
            last_offset = f.tell() - self.row_size

            if offset != last_offset:
                # move the last row into the gap left by the deleted row
                f.seek(last_offset)
                last_row_data = f.read(self.row_size)
                f.seek(offset)
                f.write(last_row_data)

                moved_row = self._unpack_row(last_row_data)
                moved_key = str(moved_row[self.primary_key])
                self.key_index[moved_key] = offset

            f.truncate(last_offset)

        del self.key_index[str(key)]
        self._save_index()
        return True


