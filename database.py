from helpers import *

def initialize_database() :
    import sqlite3 as sql
    """ Define the Database connection """
    db = sql.connect ( "chia-farm-stats.db" )
    with db :
        db.execute ( "CREATE TABLE if not exists plots (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, name TEXT, path TEXT,drive TEXT,size FLOAT, type TEXT, valid TEXT); " )
        db.execute ( "CREATE UNIQUE INDEX if not exists idx_plots_name ON plots ( name );" )

        db.execute ( "CREATE TABLE if not exists plot_directory ( id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, path TEXT, drive TEXT, type TEXT, valid TEXT);" )
        db.execute ( "CREATE UNIQUE INDEX if not exists idx_plot_directory_oath ON plot_directory ( path );" )

        ## clean up from previous versions
        db.execute ( "DROP INDEX if exists idx_plots_name;" )
        db.execute ( "DROP TABLE if exists farm;" )


