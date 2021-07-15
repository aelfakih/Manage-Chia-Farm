from helpers import *

def initialize_database() :
    import sqlite3 as sql
    """ Define the Database connection """
    if not os.path.exists ( 'db' ) :
        os.makedirs ( 'db' )
    db = sql.connect ( "db\chia-farm-stats.db" )
    with db :
        db.execute ( "CREATE TABLE if not exists plots (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, name TEXT, path TEXT,drive TEXT,size FLOAT, type TEXT, valid TEXT, unique(name)); " )
        db.execute ( "CREATE TABLE if not exists plot_directory ( id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, path TEXT, drive TEXT, drive_size FLOAT, drive_used FLOAT, drive_free FLOAT, valid TEXT, unique(path));" )

        # Commit your changes in the database
        db.commit ( )
    print("* Initializing Database...")


