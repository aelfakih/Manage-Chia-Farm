# -*- coding: utf-8 -*-
import os
import sqlite3 as sql
import logging


def initialize_database() :
    """ Define the Database connection """
    if not os.path.exists ( 'db' ) :
        os.makedirs ( 'db' )

    database = get_db_path() + "chia-farm-stats.db"

    db = sql.connect ( database )
    c = db.cursor ( )
    with db :
        db.execute ( "CREATE TABLE if not exists plots (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, name TEXT, path TEXT,drive TEXT,size FLOAT, type TEXT, valid TEXT, date REAL DEFAULT (datetime('now','localtime')),unique(name)); " )
        db.execute ( "CREATE TABLE if not exists plot_directory ( id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, path TEXT, drive TEXT, drive_size FLOAT, drive_used FLOAT, drive_free FLOAT, valid TEXT, date REAL DEFAULT (datetime('now','localtime')), unique(path));" )

        # add logic to manage scan_keys
        db.execute ( "CREATE TABLE if not exists farm_scan ( id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, initiated_by TEXT, scan_ukey TEXT, date REAL DEFAULT (datetime('now','localtime')), unique(scan_ukey));" )

        c.execute("SELECT * FROM pragma_table_info('plots') WHERE name = 'scan_ukey';")
        data = c.fetchall ( )
        if len(data) == 0:
            db.execute ( "ALTER TABLE plots ADD column scan_ukey TEXT;" )

        c.execute("SELECT * FROM pragma_table_info('plot_directory') WHERE name = 'scan_ukey';")
        data = c.fetchall ( )
        if len(data) == 0:
            db.execute ( "ALTER TABLE plot_directory ADD column scan_ukey TEXT;" )

        # Commit your changes in the database
        db.commit ( )
    print("* Initializing Database...")

def get_results_from_database(sql_query) :
    from helpers import is_verbose
    db = db_connect ( )
    c = db.cursor ( )
    c.execute ( sql_query )
    data = c.fetchall ( )
    if is_verbose ( ) :
        logging.debug ( sql_query )
    return data


def do_changes_to_database(sql_query) :
    from helpers import is_verbose
    db = db_connect ( )
    c = db.cursor ( )
    c.execute ( sql_query )
    if is_verbose ( ) :
        logging.debug ( sql_query )
    db.commit()
    return

def db_connect() :
    database = get_db_path() + "chia-farm-stats.db"
    db = sql.connect ( database )
    return db


def get_db_path() :
    from helpers import get_config
    import os, logging

    db_path = get_config ( 'config.yaml' ).get ( 'database_location' )

    if db_path:
        path = os.path.join(db_path, '')
        if not os.path.exists(path):
            logging.error(f"! Directory [{db_path}] 'database_location' in config.yaml does not exist")
            print(f"! Directory [{db_path}] 'database_location' in config.yaml does not exist")
            exit()
        else:
            return path

    else:
        return os.path.join("db", '')





