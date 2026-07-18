from lexer import tokenize
from parser import parser
import os
import sys
 
# Assets/ lives OUTSIDE this folder (one level up), so add the parent
# folder to Python's search path before importing from it.
_PARENT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PARENT_FOLDER not in sys.path:
    sys.path.append(_PARENT_FOLDER)
from CraftDB.StorageEngine import StorageEngine
from CraftDB.SemanticAnalyzer import  SemanticAnalyzer
from CraftDB.Executor import Executor



def main():



    query = """
    # craft database TEMP;
    craft database use TEMP;
    # craft database show;
    # Craft database drop mydb; -- need to add
    craft table users(
        id:int,
        name:string,
        age:int,
        primary(id)
    );

    # craft table users(
    #     id:int,
    #     name:string,
    #     age:int,
    #     temp:float
    # );

    # craft table drop users; -- need to add

    # craft table show; -- need to add

    # craft table describe users; -- need to add



    # craft table rename mydb to users;

    craft insert users (id, name, age ) ["1", "John", "30"];
    # craft insert users (id, name, age ) ["2", "Jane", "25"], ["3", "Bob", "40"];
    # # # for all queries
    # craft insert users ["2", "Jane", "25"],["3", "Bob", "40"];
    # craft from users * where age > 30 order by name asc limit 10;
    # craft from users age where age < 30 order by name desc limit 5;
    # craft from users name,age where age >= 18 and age <= 65 order by name asc limit 20;
    # craft from users name,age where age >= 18 or age <= 65 order by name desc limit 15;
    # craft from users name,age where age != 30 order by name asc limit 10;
    # craft from users name,age where age = 30 order by name desc limit 5;

    # craft update users set age = 31 where id = 1;
    # craft update users set name = "John Doe" where id = 1;
    # craft update users set age = 32, name = "John Smith" where id = 1;
    # craft update users set qty = 33.12, name = "John Doe" where id = 1 and name = "John Smith";
    # craft update users set age = 34 where id = 1 or name = "John Doe";
    # craft update users set age = 35 where id = 1 and name = "John Doe" or age = 30;

    # craft delete from users where id = 1;
    # craft delete from users where name = "John Doe";
    # craft delete from users where age > 30;
    # craft delete from users where age < 30 and name = "Jane Doe";
    # craft delete from users where age >= 18 or age <= 65;

    """


    tokens = tokenize(query)
    # for token in tokens:
    #     print(token)
    Abstract_Syntax_Tree = parser(tokens)

    print("Initiating Storage Engine...")
    storage = StorageEngine()
    print("Storage Engine Initiated Successfully")
    print("Inititating SematicAnalyzer..")
    analyzer = SemanticAnalyzer(storage)
    
    print("Initited SematicAnalyzer Successfully")
    queries = analyzer.analyze(Abstract_Syntax_Tree)
    executor = Executor()
    print(queries)
    result = []
    for query in queries:

        if(query["status"]!="OK"):
            raise Exception("Invalid Query")
        output = executor.execute_query(query["statement"])
        result.append(output)
    print(result)
        
        

    


main()
#
# #{
#   "ok": true,
#   "result": [
#     [
#       "users"
#     ]
#   ]
# }
# {
#   "ok": true,
#   "result": [
#     {
#       "columns": {
#         "age": "int",
#         "id": "int",
#         "name": "string"
#       },
#       "primary_key": "id"
#     }
#   ]
# }
# {
#   "ok": true,
#   "result": [
#     {
#       "result": [
#         "test"
#       ],
#       "result_type": "list"
#     }
#   ]
# }


    