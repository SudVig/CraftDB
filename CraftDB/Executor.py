from CraftDB.StorageEngine import StorageEngine

class Executor:

    def __init__(self):
        self.StorageEngine = StorageEngine()
        self.current_db = self.StorageEngine.get_current_database()
        pass
    def get_db_list(self):
        result = self.StorageEngine.list_databases()
        return {"result_type": "list","result": result}
    def create_db(self,db_name):

        if self.StorageEngine.database_exists(db_name):
            return {"result_type":"Error","result":f"{db_name} already exsist "}
        
        result = self.StorageEngine.create_database(db_name)
        if(not result):
            return {"result_type":"Error","result":f"Unexpected Error occured while creating {db_name}"}
        return {"result_type":"string","result":f"{db_name} Created Successfully"}


    
    def initialize_db(self,db_name):

        result = self.StorageEngine.set_current_database(db_name)
        if(not result):
            return {"result_type": "string","result": "Unable to set the database"}
        return {"result_type": "string","result": f"{db_name} set as current database"}
    
    def create_table(self,table_name,columns,primary_key):
        result = self.StorageEngine.create_table(db_name=self.current_db, table_name=table_name, columns=columns, primary_key=primary_key)
        
        if(result):
            return {"result_type": "string","result": "Table Created Successfully"}
        return {"result_type": "error","result": "Table Creation is unsuccessful, table might be present already"}
    
    def drop_db(self,db_name):
        result = self.StorageEngine.drop_database(db_name)
        if(result):
            return {"result_type": "string","result": f"{db_name} dropped Successfully"}
        return {"result_type": "error","result": "Database drop is unsuccessful, Database may not exist"}

    def drop_table(self,db_name,table_name):
        result = self.StorageEngine.drop_table(db_name,table_name)
        if(result):
            return {"result_type": "string","result": f"{table_name} dropped Successfully"}
        return {"result_type": "error","result": "Table drop is unsuccessful, Database may not exist"}
        
    
    def insert_into_tables(self,table_name,columns,values):
        result = self.StorageEngine.insert_into_table(table_name,columns,values)
        if(result):
            return {"result_type": "string","result": "Records inserted successfully"}
        return {"result_type": "error","result": "Records not inserted due to some issue"}
    def get_current_db(self):
        return self.StorageEngine.get_current_database()
    def get_table_list(self):
        db_name = self.get_current_db()
        return self.StorageEngine.list_tables(db_name)
    def get_table_schema(self,table_name):
        db_name = self.get_current_db()
        return self.StorageEngine.get_table_schema(db_name,table_name)
    def change_table_name(self,old_name,new_name):
        db_name = self.get_current_db()
        self.StorageEngine.change_table_name(db_name,old_name,new_name)
        return {"result_type": "message","result": f"Table renamed from \'{old_name}\' to \'{new_name}\'"}
        

    def execute_query(self,query):

        query_type = query["type"]
        if query_type not in ("insert"):
            action = query["action"]
            

        if(query_type=="database"):

            if(action=="show"):
                
                result = self.get_db_list()
                temp=[]
                for i in result["result"]:
                    temp.append({"database_name":i})
                
                    

                return {"result_type": "list","result":temp}

            
            elif(action=="create"):
                db_name = query["name"]
                return self.create_db(db_name)
            
            elif(action=="use"):
                db_name = query["name"]
                return self.initialize_db(db_name=db_name)
            elif(action=="drop"):
                db_name = query["name"]
                return self.drop_db(db_name)

        elif(query_type=="table"):

            if(action=="create"):

                result =  self.create_table(table_name=query["name"],columns=query["columns"],primary_key=query["primary_key"])
                return result
            elif(action=="drop"):
                db_name = self.get_current_db()
                result = self.drop_table(db_name,table_name=query["name"])
                return result
            elif(action=="show"):
                result = self.get_table_list()
                
                temp=[]
                for i in result:
                    temp.append({"table_name":i})

                return {"result_type": "list","result":temp}
            elif(action=="describe"):
                
                result = self.get_table_schema(table_name=query["name"])
                
                temp=[]
                for i,j in result["columns"].items():
                    row = {"Column":i,"Data type":j}
                    temp.append(row)

                return {"result_type": "list","result":temp}
            elif(action=="rename"):
                
                old_name = query["old_name"]
                new_name = query["new_name"]
                result = self.change_table_name(old_name,new_name)
                return result

        elif(query_type=="insert"):

            table_name = query["table"]
            columns = query["columns"]
            values = query["values"]

            if(len(columns)==0):
                table_structure = self.StorageEngine.get_table_schema(self.current_db,table_name)
                
                columns = list(table_structure["columns"].keys())

            result = self.insert_into_tables(table_name=table_name,columns = columns,values=values)

            return result
        
        elif query_type == "select":
            table_name = query["table"]
            columns = query["columns"]
            where = query["where"]
            order_by = query.get("order_by")
            limit = query.get("limit")

            

            result = self.StorageEngine.select_from_table(
                table_name=table_name,
                columns=columns,
                where=where,
                order_by=order_by,
                limit=limit,
            )

            if result is False:
                return {"result_type": "error", "result": f"Table '{table_name}' does not exist"}

            return {"result_type": "list", "result": result}
            
        elif query_type=="update":
            
            table_name = query["table"]
            columns = {i["column"]: i["value"] for i in query["set"]}
            where = query["where"]
          
            result = self.StorageEngine.update(table_name=table_name,updates=columns,where=where)
            if result is False:
                return {"result_type": "error", "result": f"Error occured while updating.."}

            return {"result_type": "message", "result": "Updated Successfully"}
        elif query_type == "delete":
            table_name = query["table"]
            where = query["where"]
            result = self.StorageEngine.delete_from_table(table_name=table_name, where=where)
            if result is False:
                return {"result_type": "error", "result": f"Error occured while Deleting.."}

            return {"result_type": "message", "result": f"Deleted Successfully" }
        

            

                

        
        return {"result_type": "error","result": "Unexpected Query"}

            


        
        

        

