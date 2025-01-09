import psycopg2

DATABASE_URL = 'postgresql://postgres:qweasdzxc@localhost:5432/diplom'

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)