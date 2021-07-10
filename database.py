def initialize_database() :
    """ Define the Database connection """
    db = sql.connect ( "sinoda.db" )
    with db :
        db.execute ( """
             CREATE TABLE if not exists plots (
                 id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                 name TEXT,
                 path TEXT,
                 drive TEXT,
                 size FLOAT,
                 last);
                 """ )
        db.execute ( """
             CREATE TABLE if not exists farm (
                 id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                 plot TEXT,
                 path TEXT,
                 drive TEXT,
                 updatedatetime text DEFAULT (strftime('%Y-%m-%d %H:%M:%S:%s','now', 'localtime')));
                 """ )
        db.execute ( "CREATE UNIQUE INDEX if not exists idx_farm_plot ON farm ( plot );" )
