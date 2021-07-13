from helpers import *

def initialize_database() :
    import sqlite3 as sql
    """ Define the Database connection """
    db = sql.connect ( "chia-farm-stats.db" )
    with db :
        db.execute ( "CREATE TABLE if not exists plots (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, name TEXT, path TEXT,drive TEXT,size FLOAT, type TEXT, valid TEXT); " )
        db.execute ( "CREATE TABLE if not exists farm ( id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, plot TEXT, path TEXT, drive TEXT);" )
        db.execute ( "CREATE UNIQUE INDEX if not exists idx_farm_plot ON farm ( plot );" )
        #db.execute ( "CREATE UNIQUE INDEX if not exists idx_plots_name ON plots ( name );" )


def save_plot_directory(dir):
    import sqlite3 as sql
    from datetime import datetime
    import pathlib
    import logging

    db = db_connect ( )
    # Creating a cursor object using the cursor() method
    c = db.cursor ( )
    time = datetime.now ( ).strftime ( "%B %d, %Y %I:%M%p" )

    p = pathlib.Path ( dir )
    parts_length = len ( p.parts )
    drive = pathlib.Path ( dir ).parts[0]
    path = []

    if parts_length > 1 :
        path = pathlib.Path ( dir ).parts[1]

    SQLQ = "REPLACE INTO farm (plot, path, drive) values ('%s','%s','%s')" % (dir , path , drive)

    c.execute ( SQLQ )

    if is_verbose ( ) :
        logging.info ( SQLQ )

    # Commit your changes in the database
    db.commit()
    # Closing the connection
    db.close ( )


