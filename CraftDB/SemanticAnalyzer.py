"""
semantic_analyzer.py

Walks through a list of parsed statements (your AST) and checks that
each one makes sense against the CURRENT metadata:

    - does the database exist?
    - is a database currently selected (USE)?
    - does the table exist?
    - do the referenced columns exist?
    - does the value's type match the column's declared datatype?

This does NOT execute the query (no rows are touched) — it only
validates. DDL statements (CREATE/USE/DROP DATABASE, CREATE/DROP/
RENAME TABLE) DO update the tracked metadata as they're checked,
because later statements in the same list depend on that metadata
existing (e.g. you can't validate an INSERT into 'users' unless
'users' was already recorded by an earlier CREATE TABLE check).
"""


class SemanticError(Exception):
    pass


class SemanticAnalyzer:
    # maps CraftQL datatype names -> the Python type they should match
    DATATYPE_MAP = {
        "int": int,
        "string": str,
        "float": float,
    }

    def __init__(self, storage_engine):
        self.storage = storage_engine
        self.current_database = self.storage.get_current_database()

    # -- public entry point --------------------------------------------------

    def analyze(self, ast_list):
        """
        Checks every statement in order. Returns a report list:
            [{"index": 0, "status": "OK", ...}, {"index": 1, "status": "ERROR", "message": ...}, ...]
        """
        report = []
        for index, statement in enumerate(ast_list):
            try:
                self._check_statement(statement)
                report.append({"index": index, "statement": statement, "status": "OK"})
            except SemanticError as error:
                report.append({
                    "index": index,
                    "statement": statement,
                    "status": "ERROR",
                    "message": str(error),
                })
        return report

    # -- dispatch --------------------------------------------------------------

    def _check_statement(self, stmt):
        stmt_type = stmt.get("type")

        if stmt_type == "database":
            self._check_database_statement(stmt)
        elif stmt_type == "table":
            self._check_table_statement(stmt)
        elif stmt_type == "insert":
            self._check_insert(stmt)
        elif stmt_type == "select":
            self._check_select(stmt)
        elif stmt_type == "update":
            self._check_update(stmt)
        elif stmt_type == "delete":
            self._check_delete(stmt)
        else:
            raise SemanticError(f"Unknown statement type: {stmt_type!r}")

    # -- DATABASE ------------------------------------------------------------------

    def _check_database_statement(self, stmt):
        action = stmt["action"]

        if action == "create":
            name = stmt["name"]
            if self.storage.database_exists(name):
                raise SemanticError(f"Database '{name}' already exists.")

        elif action == "use":
            name = stmt["name"]
            if not self.storage.database_exists(name):
                raise SemanticError(f"Database '{name}' does not exist.")

        elif action == "drop":
            name = stmt["name"]
            if not self.storage.database_exists(name):
                raise SemanticError(f"Database '{name}' does not exist.")

        elif action == "show":
            pass  # nothing to validate

        else:
            raise SemanticError(f"Unknown database action: {action!r}")

    # -- TABLE ------------------------------------------------------------------------

    def _check_table_statement(self, stmt):
        action = stmt["action"]
        self._require_database_selected()

        if action == "create":
            name = stmt["name"]
            if self.storage.table_exists(self.current_database, name):
                raise SemanticError(
                    f"Table '{name}' already exists in database '{self.current_database}'."
                )

            seen_columns = set()
            for col in stmt["columns"]:
                if col["datatype"] not in self.DATATYPE_MAP:
                    raise SemanticError(
                        f"Unknown datatype '{col['datatype']}' for column '{col['name']}'."
                    )
                if col["name"] in seen_columns:
                    raise SemanticError(f"Duplicate column name '{col['name']}' in table '{name}'.")
                seen_columns.add(col["name"])

            primary_key = stmt.get("primary_key")
            if primary_key is not None and primary_key not in seen_columns:
                raise SemanticError(
                    f"Primary key '{primary_key}' is not a column of table '{name}'."
                )

            

        elif action == "drop":
            name = stmt["name"]
            if not self.storage.table_exists(self.current_database, name):
                raise SemanticError(
                    f"Table '{name}' does not exist in database '{self.current_database}'."
                )

        elif action == "show":
            pass

        elif action == "describe":
            name = stmt["name"]
            if not self.storage.table_exists(self.current_database, name):
                raise SemanticError(
                    f"Table '{name}' does not exist in database '{self.current_database}'."
                )

        elif action == "rename":
            old_name, new_name = stmt["old_name"], stmt["new_name"]
            if not self.storage.table_exists(self.current_database, old_name):
                raise SemanticError(
                    f"Table '{old_name}' does not exist in database '{self.current_database}'."
                )
            if self.storage.table_exists(self.current_database, new_name):
                raise SemanticError(
                    f"Table '{new_name}' already exists in database '{self.current_database}'."
                )

        else:
            raise SemanticError(f"Unknown table action: {action!r}")

    # -- INSERT --------------------------------------------------------------------------

    def _check_insert(self, stmt):
        self._require_database_selected()
        table = stmt["table"]
        schema = self._require_table(table)

        # if no column list given, assume values are in schema-declared order
        columns = stmt["columns"] if stmt["columns"] else list(schema["columns"].keys())

        unknown_columns = set(columns) - set(schema["columns"].keys())
        if unknown_columns:
            raise SemanticError(f"Column(s) {sorted(unknown_columns)} do not exist in table '{table}'.")

        for row in stmt["values"]:
            if len(row) != len(columns):
                raise SemanticError(
                    f"Table '{table}': expected {len(columns)} value(s) but got {len(row)}."
                )
            for col_name, raw_value in zip(columns, row):
                datatype = schema["columns"][col_name]
                self._check_value_type(col_name, raw_value, datatype, already_typed=False)

    # -- SELECT ---------------------------------------------------------------------------

    def _check_select(self, stmt):
        self._require_database_selected()
        table = stmt["table"]
        schema = self._require_table(table)

        if stmt["columns"] != ["*"]:
            for col in stmt["columns"]:
                self._require_column(table, schema, col)

        self._check_where(table, schema, stmt.get("where"))

        order_by = stmt.get("order_by")
        if order_by:
            self._require_column(table, schema, order_by["column"])

    # -- UPDATE --------------------------------------------------------------------------

    def _check_update(self, stmt):
        self._require_database_selected()
        table = stmt["table"]
        schema = self._require_table(table)

        for change in stmt["set"]:
            col_name = change["column"]
            if col_name not in schema["columns"]:
                raise SemanticError(f"Column '{col_name}' does not exist in table '{table}'.")
            self._check_value_type(col_name, change["value"], schema["columns"][col_name], already_typed=True)

        self._check_where(table, schema, stmt.get("where"))

    # -- DELETE --------------------------------------------------------------------------

    def _check_delete(self, stmt):
        self._require_database_selected()
        table = stmt["table"]
        schema = self._require_table(table)
        self._check_where(table, schema, stmt.get("where"))

    # -- shared helpers --------------------------------------------------------------------

    def _require_database_selected(self):
        if self.current_database is None:
            raise SemanticError("No database selected. Run 'craft use <database>;' first.")

    def _require_table(self, table):
        if not self.storage.table_exists(self.current_database, table):
            raise SemanticError(
                f"Table '{table}' does not exist in database '{self.current_database}'."
            )
        return self.storage.get_table_schema(self.current_database, table)

    def _require_column(self, table, schema, column):
        if column not in schema["columns"]:
            raise SemanticError(f"Column '{column}' does not exist in table '{table}'.")

    def _check_where(self, table, schema, where_clauses):
        if not where_clauses:
            return
        for clause in where_clauses:
            if clause in ("AND", "OR"):   # logical connector between conditions, skip
                continue
            column = clause["left"]
            self._require_column(table, schema, column)
            datatype = schema["columns"][column]
            self._check_value_type(column, clause["right"], datatype, already_typed=True)

    def _check_value_type(self, column, value, datatype, already_typed):
        expected_type = self.DATATYPE_MAP.get(datatype)
        if expected_type is None:
            raise SemanticError(f"Unknown datatype '{datatype}' for column '{column}'.")

        if already_typed:
            # value is already a real Python int/float/str/bool (e.g. from WHERE/SET)
            if expected_type is float and isinstance(value, int):
                return  # a whole number is fine where a float is expected
            if not isinstance(value, expected_type) or isinstance(value, bool) != (expected_type is bool):
                raise SemanticError(
                    f"Type mismatch for column '{column}': expected {datatype}, "
                    f"got {type(value).__name__} ({value!r})."
                )
        else:
            # value came in as a raw string (e.g. from INSERT) — check it CAN convert
            try:
                expected_type(value)
            except (ValueError, TypeError):
                raise SemanticError(
                    f"Type mismatch for column '{column}': expected {datatype}, got value {value!r}."
                )