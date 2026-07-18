"""
storage_engine.py

FilesIOEngine  -> ONLY reads/writes raw .cdb files (with a version header).
StorageEngine  -> uses FilesIOEngine to track metadata:
                    - which databases exist, which one is "in use"
                    - which tables exist in each database, their columns/
                      datatypes/primary key
                  and uses BPlusTree (disk_bplus_tree.py) to actually
                  store/retrieve/update/delete rows for each table.

Metadata is kept as JSON inside the .cdb files, right after a small
plain-text version header.
"""

import os
import sys
import json


# Assets/ lives OUTSIDE this folder (one level up), so add the parent
# folder to Python's search path before importing from it.
_PARENT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PARENT_FOLDER not in sys.path:
    sys.path.append(_PARENT_FOLDER)

from CraftDB.FileIOEngine import FilesIOEngine
from CraftDB.BplusTree import BPlusTree

from Assets.Env import DATABASES_PATH, TABLES_PATH, VERSION, DATABASE_FOLDER_PATH




class StorageEngine:
    """
    Sits on top of FilesIOEngine. This is what the rest of the engine
    (parser/executor/semantic analyzer) actually talks to.

    Tracks:
      - database_meta = {"databases": [...], "current": "mydb" or None}
      - table_meta     = {"mydb": {"users": {"columns": {...}, "primary_key": "id"}}}
      - _engines       = {(db_name, table_name): BPlusTree instance}  (in-memory cache)
    """

    def __init__(self):
        
        self.io = FilesIOEngine()
        self.database_meta = self.io.read_file(
            self.io.databases_path, default={"databases": [], "current": None}
        )
        self.table_meta = self.io.read_file(self.io.tables_path, default={})
        self._engines = {}
            # -- metadata refresh ---------------------------------------------------
    def _refresh_metadata(self):
        self.database_meta = self.io.read_file(
            self.io.databases_path,
            default={"databases": [], "current": None},
        )
        self.table_meta = self.io.read_file(
            self.io.tables_path,
            default={},
        )
    # -- persistence helpers ------------------------------------------------
    def _save_databases(self):

        self.io.write_file(self.database_meta, self.io.databases_path)

    def _save_tables(self):
        self.io.write_file(self.table_meta, self.io.tables_path)

    # -- DATABASE operations --------------------------------------------------
    def database_exists(self, name):
        self._refresh_metadata()
        return name in self.database_meta["databases"]

    def create_database(self, db_name):
        self._refresh_metadata()
        is_db_created = self.io.create_db_folder(db_name)
        if(is_db_created):
            self.database_meta["databases"].append(db_name)
            self.table_meta[db_name] = {}
            self._save_databases()
            self._save_tables()
        return is_db_created

    def drop_database(self, name):
        self._refresh_metadata()
        is_db_droped = self.io.delete_db_folder(name)

        if is_db_droped:
            self.database_meta["databases"].remove(name)
            self.table_meta.pop(name, None)
            if self.database_meta["current"] == name:
                self.database_meta["current"] = None
            self._save_databases()
            self._save_tables()
        
        return is_db_droped

    def set_current_database(self, name):
        self._refresh_metadata()
        if self.database_exists(name):
            self.database_meta["current"] = name
            self._save_databases()
        else:
            return False
        return True

    def get_current_database(self):
        self._refresh_metadata()
        return self.database_meta.get("current")

    def list_databases(self):
        self._refresh_metadata()
        return list(self.database_meta["databases"])

    # -- TABLE operations ----------------------------------------------------
    def table_exists(self, db_name = None, table_name = None):
        self._refresh_metadata()
        if db_name is None:
            db_name = self.get_current_database()

        
        
        

        return db_name in self.table_meta and table_name in self.table_meta[db_name]
    


    def create_table(self, db_name = None, table_name = None, columns = None, primary_key = None):
        self._refresh_metadata()
        if db_name is None :
            db_name = self.get_current_database()
        """columns is a list like [{"name": "id", "datatype": "int"}, ...]"""
        result = self.table_exists(db_name,table_name)
        
        if(not result):
            self.io.create_table_file(db_name,table_name)
            self.table_meta.setdefault(db_name, {})[table_name] = {
                "columns": {col["name"]: col["datatype"] for col in columns},
                "primary_key": primary_key,
            }
            self._save_tables()

        else:

            return False
        return True


    def drop_table(self, db_name, table_name):
        self._refresh_metadata()
        is_table_droped = self.io.drop_table_file(db_name,table_name)
        if is_table_droped:
            del self.table_meta[db_name][table_name]
            self._save_tables()
            self._engines.pop((db_name, table_name), None)

        return is_table_droped

    def rename_table(self, db_name, old_name, new_name):
        self._refresh_metadata()
        self.io.rename_table_file(db_name,old_name,new_name)
        self.table_meta[db_name][new_name] = self.table_meta[db_name].pop(old_name)
        self._save_tables()

    def get_table_schema(self, db_name, table_name):
        self._refresh_metadata()
        """Returns {"columns": {"id": "int", ...}, "primary_key": "id"}"""
        
        return self.table_meta[db_name][table_name]
    def get_table_primary_key(self, db_name, table_name):
        self._refresh_metadata()
        """Returns {"columns": {"id": "int", ...}, "primary_key": "id"}"""
        return self.table_meta[db_name][table_name]

    def list_tables(self, db_name):
        self._refresh_metadata()
        return list(self.table_meta.get(db_name, {}).keys())

    # -- ROW ENGINE ------------------------------------------------------------

    def _get_engine(self, db_name, table_name):
        """
        Returns a cached BPlusTree instance for this table, built from the
        schema stored in table_meta. Cached per (db, table) so the in-memory
        key_index doesn't get reloaded from disk on every single call.
        """
        key = (db_name, table_name)
        
        if key not in self._engines:
            schema = self.get_table_schema(db_name, table_name)
            
            db_path = os.path.join(DATABASE_FOLDER_PATH, db_name)
            self._engines[key] = BPlusTree(
                table_name=table_name,
                schema=schema["columns"],
                primary_key=schema["primary_key"],
                db_path=db_path,
            )
            
        return self._engines[key]

    # -- ROW operations: insert / select / update / delete ----------------------

    def insert_into_table(self, table_name, columns, values):
        """
        columns: ["id", "name", "score"]
        values:  [[1, "alice", 100], [2, "bob", 90]]   <- list of rows
        """
        db_name = self.get_current_database()
        if not self.table_exists(db_name, table_name):
            return False

        engine = self._get_engine(db_name, table_name)
        for value_set in values:
            row = dict(zip(columns, value_set))
            engine.insert(row)
        return True

    def select_from_table(self, table_name, columns, where, order_by, limit):
        """
        where: None (or []) -> all rows
        where: [{"left": "age", "operator": ">=", "right": 18}, "AND", {...}]
        """

        db_name = self.get_current_database()
        if not self.table_exists(db_name, table_name):
            return False
        engine = self._get_engine(db_name, table_name)
        return engine.select(columns, where, order_by, limit)
    
    def update(self, table_name, updates, where=None):
        """
        updates: {"score": 0}
        where:   None (or []) -> updates every row
                 or a condition list, same format as select
        Returns the number of rows updated.
        """
        db_name = self.get_current_database()
        if not self.table_exists(db_name, table_name):
            return False
        engine = self._get_engine(db_name, table_name)
        pk_key = self.get_table_primary_key(db_name=db_name,table_name=table_name)["primary_key"]
        key=None
        
        if(pk_key in updates):
            key=pk_key

        # engine.update_key(3, {"score": 95})
        return engine.update(updates=updates,key=key,where=where)

    def delete_from_table(self, table_name, where=None):
        """
        where: None (or []) -> deletes every row in the table
               or a condition list, same format as select
        Returns the number of rows deleted.
        """
        db_name = self.get_current_database()
        if not self.table_exists(db_name, table_name):
            return False

        engine = self._get_engine(db_name, table_name)
        return engine.delete(key=None,where= where or [])
    
    def change_table_name(self,db_name,old_name,new_name):

        result = self.rename_table(db_name,old_name,new_name)
        return result
    
    

        