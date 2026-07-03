from lexer import tokenize
from parser import parser

def main():
    query = """
    craft database use mydb;
    craft table users(
        id:int,
        name:text,
        age:int,
        primarykey(id)
    );
    """

    query = """

craft database mydb;
craft database use mydb;
craft database show;
craft database drop mydb;

    """

    query = """

    craft table users(
        id:int,
        name:text,
        age:int,
        primary(id)
    );

    craft table users(
        id:int,
        name:text,
        age:int,
        temp:float
    );

    craft table drop mydb;

    craft table show;

    craft table describe users;

    craft table rename mydb to users;


    """

    query = """
    craft insert users (id, name, age ) ["1", "John", "30"];
    craft insert users (id, name, age ) ["2", "Jane", "25"], ["3", "Bob", "40"];
    # for all queries
    craft insert users ["2", "Jane", "25"],["3", "Bob", "40"];
    """

    query = """
    craft from users * where age > 30 order by name asc limit 10;
    craft from users age where age < 30 order by name desc limit 5;
    craft from users name,age where age >= 18 and age <= 65 order by name asc limit 20;
    craft from users name,age where age >= 18 or age <= 65 order by name desc limit 15;
    craft from users name,age where age != 30 order by name asc limit 10;
    craft from users name,age where age = 30 order by name desc limit 5;
    """


    tokens = tokenize(query)
    for token in tokens:
        print(token)
    Abstract_Syntax_Tree = parser(tokens)

    print(Abstract_Syntax_Tree)
main()
    