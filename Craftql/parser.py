def insert_parser(tokens, pos):

    # Implement the parsing logic for the 'insert' keyword here
    # This function should return the AST for the insert operation and the new position in the tokens list
    # craft insert <table_name> (<column1>, <column2>, ...) [<value1>, <value2>, ...];
    # craft insert <table_name> [<value1>, <value2>, ...];
    # craft insert <table_name> (<column1>, <column2>, ...) [<value1>, <value2>, ...], [<value3>, <value4>, ...];

    insert_ast = {
        "type": "insert",
        "table": None,
        "columns": [],
        "values": []
    }

    if tokens[pos]["type"] != "IDENTIFIER":
        raise ValueError("Expected table name after 'insert'")

    insert_ast["table"] = tokens[pos]["value"]
    pos += 1

    if pos < len(tokens) and tokens[pos]["type"] == "LPAREN":
        pos += 1
        while pos < len(tokens) and tokens[pos]["type"] != "RPAREN":
            if tokens[pos]["type"] != "IDENTIFIER":
                raise ValueError("Expected column name")
            insert_ast["columns"].append(tokens[pos]["value"])
            pos += 1
            if pos < len(tokens) and tokens[pos]["type"] == "COMMA":
                pos += 1

        if pos >= len(tokens) or tokens[pos]["type"] != "RPAREN":
            raise ValueError("Expected ')' after column names")
        pos += 1

    if pos >= len(tokens) or tokens[pos]["type"] != "LBRACKET":
        raise ValueError("Expected '[' before values")

    while pos < len(tokens) and tokens[pos]["type"] == "LBRACKET":
        pos += 1
        value_set = []
        while pos < len(tokens) and tokens[pos]["type"] != "RBRACKET":
            if tokens[pos]["type"]!="KEYWORD" and tokens[pos]["type"]!="IDENTIFIER" and tokens[pos]["type"]!="STRING" and tokens[pos]["type"]!="NUMBER":
                raise ValueError("Expected value")
            value_set.append(tokens[pos]["value"])
            pos += 1
            if pos < len(tokens) and tokens[pos]["type"] == "COMMA":
                pos += 1

        if pos >= len(tokens) or tokens[pos]["type"] != "RBRACKET":
            raise ValueError("Expected ']' after values")

        insert_ast["values"].append(value_set)
        pos += 1

        if pos < len(tokens) and tokens[pos]["type"] == "COMMA":
            pos += 1

    if pos >= len(tokens) or tokens[pos]["type"] != "SEMICOLON":
        raise ValueError("Expected ';' after insert statement")

    pos += 1
    return insert_ast, pos

def database_parser(tokens, pos):
    # Implement the parsing logic for the 'database' keyword here
    # This function should return the AST for the database operation and the new position in the tokens list
    # craft database mydb;
    # craft database use mydb;
    # craft database show;
    # craft database drop mydb;
    # CREATE 
    # {
    #     "type": "database",
    #     "action": "create",
    #     "name": "mydb"
    # }
    
    # USE
    # {
    #    "type": "database",
    #    "action": "use",
    #    "name": "mydb"
    # }
    
    # DROP
    # {
    #    "type": "database",
    #    "action": "drop",
    #    "name": "mydb"
    
    # }
    # SHOW
    # {
    #    "type": "database",
    #    "action": "show"
    # }
    database_ast = {}
    
    while pos < len(tokens):
        print(f"Current token: {tokens[pos]} at position {pos} and type is {tokens[pos]['type']} and value is {tokens[pos]['value']}")
        if pos < len(tokens) and tokens[pos]['type'] == 'IDENTIFIER':
            database_ast['type'] = 'database'
            database_ast['action'] = 'create'
            database_ast['name'] = tokens[pos]['value']
            pos += 1
        elif pos < len(tokens) and tokens[pos]['type'] == 'KEYWORD' and tokens[pos]['value'] == 'use':
            database_ast['type'] = 'database'
            database_ast['action'] = 'use'
            pos += 1
            if pos < len(tokens) and tokens[pos]['type'] == 'IDENTIFIER':
                database_ast['name'] = tokens[pos]['value']
                pos += 1
            else:
                raise ValueError(f"Expected database name after 'use' keyword at line {tokens[pos]['line']} column {tokens[pos]['column']}")
        elif pos < len(tokens) and tokens[pos]['type'] == 'KEYWORD' and tokens[pos]['value'] == 'drop':
            database_ast['type'] = 'database'
            database_ast['action'] = 'drop'
            pos += 1
            if pos < len(tokens) and tokens[pos]['type'] == 'IDENTIFIER':
                database_ast['name'] = tokens[pos]['value']
                pos += 1
            else:
                raise ValueError(f"Expected database name after 'drop' keyword at line {tokens[pos]['line']} column {tokens[pos]['column']}")
        elif pos < len(tokens) and tokens[pos]['type'] == 'KEYWORD' and tokens[pos]['value'] == 'show':
            database_ast['type'] = 'database'
            database_ast['action'] = 'show'
            pos += 1
        elif pos < len(tokens) and tokens[pos]['type'] == 'SEMICOLON':

            pos += 1
            break
        else:
            raise ValueError(f"Expected action (create, use, drop, show) after 'database' keyword at line {tokens[pos]['line']} column {tokens[pos]['column']}")
    
    return database_ast, pos
    
def table_parser(tokens, pos):

    # Implement the parsing logic for the 'table' keyword here
    # This function should return the AST for the table operation and the new position in the tokens list
    # craft table <table_name>(
    # <column>:<datatype>,
    # ...
    # primary(<column>)
    # );
    # craft show tables;
    # craft describe <table_name>;
    # craft drop table <table_name>;

    table_ast = {}

    # ---------------- CREATE TABLE ----------------
    if tokens[pos]["type"] == "IDENTIFIER":
        added={}

        table_ast = {
            "type": "table",
            "action": "create",
            "name": tokens[pos]["value"],
            "columns": [],
            "primary_key": None
        }

        pos += 1

        if tokens[pos]["type"] != "LPAREN":
            raise ValueError("Expected '(' after table name")

        pos += 1

        while pos < len(tokens):

            # End of table definition
            if tokens[pos]["type"] == "RPAREN":
                if len(table_ast["columns"]) == 0:
                    raise ValueError("Table must have at least one column")
                pos += 1
                break

            # primary(id)
            if tokens[pos]["type"] == "KEYWORD" and tokens[pos]["value"] == "primary":

                pos += 1

                if tokens[pos]["type"] != "LPAREN":
                    raise ValueError("Expected '(' after primary")

                pos += 1

                if tokens[pos]["type"] != "IDENTIFIER":
                    raise ValueError("Expected primary key column")
                if(table_ast["primary_key"]!=None):
                    raise ValueError("Only one primary key is allowed")
                table_ast["primary_key"] = tokens[pos]["value"]

                pos += 1

                if tokens[pos]["type"] != "RPAREN":
                    raise ValueError("Expected ')'")

                pos += 1

                if pos < len(tokens) and tokens[pos]["type"] == "COMMA":
                    pos += 1

                continue

            # column
            if tokens[pos]["type"] != "IDENTIFIER":
                raise ValueError("Expected column name")

            column_name = tokens[pos]["value"]
            pos += 1

            if tokens[pos]["type"] != "COLON":
                raise ValueError("Expected ':'")

            pos += 1

            if tokens[pos]["type"] != "KEYWORD":
                raise ValueError("Expected datatype")

            datatype = tokens[pos]["value"]
            if(added.get(column_name,"")==""):
                added[column_name]=datatype
                table_ast["columns"].append({
                    "name": column_name,
                    "datatype": datatype
                })
            else:
                raise ValueError(f"Duplicate column name '{column_name}'")

            pos += 1

            if pos < len(tokens) and tokens[pos]["type"] == "COMMA":
                pos += 1

        if tokens[pos]["type"] != "SEMICOLON":
            raise ValueError("Expected ';'")

        pos += 1

        return table_ast, pos

    # ---------------- DROP TABLE ----------------
    elif tokens[pos]["type"] == "KEYWORD" and tokens[pos]["value"] == "drop":

        pos += 1

        if tokens[pos]["type"] != "IDENTIFIER":
            raise ValueError("Expected table name")

        table_ast = {
            "type": "table",
            "action": "drop",
            "name": tokens[pos]["value"]
        }

        pos += 1

        if tokens[pos]["type"] != "SEMICOLON":
            raise ValueError("Expected ';'")

        pos += 1

        return table_ast, pos

    # ---------------- SHOW TABLES ----------------
    elif tokens[pos]["type"] == "KEYWORD" and tokens[pos]["value"] == "show":

        pos += 1



        table_ast = {
            "type": "table",
            "action": "show"
        }


        if tokens[pos]["type"] != "SEMICOLON":
            raise ValueError("Expected ';'")

        pos += 1

        return table_ast, pos

    # # ---------------- DESCRIBE TABLE ----------------
    elif tokens[pos]["type"] == "KEYWORD" and tokens[pos]["value"] == "describe":

        pos += 1

        if tokens[pos]["type"] != "IDENTIFIER":
            raise ValueError("Expected table name")

        table_ast = {
            "type": "table",
            "action": "describe",
            "name": tokens[pos]["value"]
        }

        pos += 1

        if tokens[pos]["type"] != "SEMICOLON":
            raise ValueError("Expected ';'")

        pos += 1

        return table_ast, pos

    elif tokens[pos]["type"] == "KEYWORD" and tokens[pos]["value"] == "rename":

        pos += 1

        if tokens[pos]["type"] != "IDENTIFIER":
            raise ValueError("Expected table name")

        old_name = tokens[pos]["value"]
        pos += 1

        if tokens[pos]["type"] != "KEYWORD" or tokens[pos]["value"] != "to":
            raise ValueError("Expected 'to'")

        pos += 1

        if tokens[pos]["type"] != "IDENTIFIER":
            raise ValueError("Expected new table name")

        new_name = tokens[pos]["value"]
        pos += 1

        table_ast = {
            "type": "table",
            "action": "rename",
            "old_name": old_name,
            "new_name": new_name
        }

        if tokens[pos]["type"] != "SEMICOLON":
            raise ValueError("Expected ';'")

        pos += 1

        return table_ast, pos
    else:
        raise ValueError(
            f"Unexpected token '{tokens[pos]['value']}' "
            f"at line {tokens[pos]['line']} column {tokens[pos]['column']}"
        )
def parser(tokens):

    AST = []

    pos = 0

    while pos < len(tokens):

        if(tokens[pos]["type"]=="EOF" and tokens[pos]["value"]==None):

            break

        print(f"Current token: {tokens[pos]} at position {pos}")
        # craft
        if tokens[pos]["type"] != "KEYWORD" or tokens[pos]["value"] != "craft":
            raise ValueError("Expected 'craft'")

        pos += 1

        if tokens[pos]["type"] != "KEYWORD":
            raise ValueError("Expected command")

        command = tokens[pos]["value"]
        pos += 1

        if command == "database":
            ast, pos = database_parser(tokens, pos)
            AST.append(ast)

        elif command == "table":
            ast, pos = table_parser(tokens, pos)
            AST.append(ast)

        elif command == "insert":
            ast, pos = insert_parser(tokens, pos)
            AST.append(ast)

        # elif command == "select":
        #     ast, pos = select_parser(tokens, pos)
        #     AST.append(ast)

        else:
            raise ValueError(f"Unknown command {command}")

    return AST