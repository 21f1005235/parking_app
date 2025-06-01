import os
basedir= os.path.abspath(os.path.dirname(__file__))


class Config():
    DEBUG=False
    SQLITE_DB_DIR=None
    SQLALCHEMY_DATABASE_URI=None
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    SECRET_KEY = "a-very-secret-key-123" 
    
class LocalDevelopmentConfig(Config):

    SQLITE_DB_DIR=os.path.join(basedir,"db_directory")
    SQLITE_DB_FILE = os.path.join(SQLITE_DB_DIR, "db.sqlite3")
    SQLALCHEMY_DATABASE_URI="sqlite:///"+SQLITE_DB_FILE
    DEBUG=True
