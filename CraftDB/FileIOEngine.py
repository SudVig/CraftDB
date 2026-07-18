"""
storage_engine.py

FilesIOEngine  -> ONLY reads/writes raw .cdb files (with a version header).
StorageEngine  -> uses FilesIOEngine to track metadata:
                    - which databases exist, which one is "in use"
                    - which tables exist in each database, their columns/
                      datatypes/primary key

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



from Assets.Env import DATABASES_PATH, TABLES_PATH, VERSION, DATABASE_FOLDER_PATH



class FilesIOEngine:
    """
    Handles ONLY read/write of .cdb files.
    File layout on disk:
        Line 1: "VERSION <version>"
        Rest:   JSON content (a dict or list)
    """

    def __init__(self):
        if not DATABASES_PATH:
            raise ValueError("ENV Error: MetaData path for Database is missing")
        if not TABLES_PATH:
            raise ValueError("ENV Error: MetaData path for Table is missing")

        self.databases_path = DATABASES_PATH
        self.tables_path = TABLES_PATH
        self.version = VERSION
        

        # make sure the folder these files live in actually exists
        for path in (self.databases_path, self.tables_path):
            folder = os.path.dirname(path)
            if folder and not os.path.exists(folder):
                os.makedirs(folder)

    def write_header(self, file_ptr):
        file_ptr.write(f"VERSION {self.version}\n")

    def check_version(self, file_ptr):
        """Reads the header line and returns the version string found, or None."""
        line = file_ptr.readline()
        if not line.startswith("VERSION"):
            return None
        return line.strip().split(" ")[1]

    def read_file(self, path, default):
        """
        Reads a .cdb file and returns its JSON content.
        If the file doesn't exist yet, creates it with `default` content
        and returns `default`.
        """
        if not os.path.exists(path):
            
            self.write_file(default, path)
            return default

        with open(path, "r") as file_ptr:
            version_found = self.check_version(file_ptr)
            if version_found != self.version:
                print(
                    f"Warning: '{path}' was written with version "
                    f"{version_found}, current engine version is {self.version}"
                )
            content = file_ptr.read().strip()
            if not content:
                return default
            return json.loads(content)

    def write_file(self, content, path):
        """Writes `content` (dict/list) to a .cdb file, with the version header."""
        with open(path, "w") as file_ptr:
            self.write_header(file_ptr)
            json.dump(content, file_ptr, indent=2)

    def create_db_folder(self,db_name):
            try:
                db_path = DATABASE_FOLDER_PATH+"/"+db_name+"/"
                folder = os.path.dirname(db_path)
                if folder and not os.path.exists(folder):
                    os.makedirs(folder,exist_ok=True)
            except:

                return False
            return True
    def delete_db_folder(self, db_name):
        try:
            db_path = DATABASE_FOLDER_PATH + "/" + db_name + "/"

            if not os.path.exists(db_path):
                
                return False

            for root, dirs, files in os.walk(db_path, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for directory in dirs:
                    os.rmdir(os.path.join(root, directory))

            os.rmdir(db_path)
            

        except Exception as e:
            
            return False

        return True

    def create_table_file(self, db_name, table_name):

        # Database folder
        db_folder = os.path.join(DATABASE_FOLDER_PATH, db_name)

        # 1. Check if database exists
        if not os.path.isdir(db_folder):
            raise Exception(f"Database '{db_name}' does not exist.")

        # Table file path
        table_path = os.path.join(db_folder, f"{table_name}.cdb")

        # 2. Check if table already exists
        if os.path.isfile(table_path):
            raise Exception(f"Table '{table_name}' already exists.")

        # 3. Create the table file
        with open(table_path, "xb") as f:
            pass

        return table_path
    
    def drop_table_file(self, db_name, table_name):

        db_folder = os.path.join(DATABASE_FOLDER_PATH, db_name)

        if not os.path.isdir(db_folder):
            raise Exception(f"Database '{db_name}' does not exist.")

        table_path = os.path.join(db_folder, f"{table_name}.cdb")
        if not os.path.isfile(table_path):
            raise Exception(f"Table '{table_name}' does not exist.")

        os.remove(table_path)

        return True
        
    def rename_table_file(self, db_name, old_table_name, new_table_name):

        db_folder = os.path.join(DATABASE_FOLDER_PATH, db_name)

        if not os.path.isdir(db_folder):
            raise Exception(f"Database '{db_name}' does not exist.")

        old_table_path = os.path.join(db_folder, f"{old_table_name}.cdb")

        new_table_path = os.path.join(db_folder, f"{new_table_name}.cdb")

        old_index_path = old_table_path + ".index.json"

        new_index_path = new_table_path + ".index.json"

        if not os.path.isfile(old_table_path):
            raise Exception(f"Table '{old_table_name}' does not exist.")


        if os.path.isfile(new_table_path):
            raise Exception(f"Table '{new_table_name}' already exists.")

        os.rename(old_table_path, new_table_path)
        
        if os.path.isfile(old_index_path):
            os.rename(old_index_path, new_index_path)

        return True
            
                
        
