import sqlite3

DB = "data/motores.db"

def conectar():
    return sqlite3.connect(DB)

def salvar_motor(marca, tensao, potencia):

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS motores(
        id INTEGER PRIMARY KEY,
        marca TEXT,
        tensao TEXT,
        potencia TEXT
    )
    """)

    cur.execute(
        "INSERT INTO motores (marca,tensao,potencia) VALUES (?,?,?)",
        (marca,tensao,potencia)
    )

    conn.commit()
    conn.close()

def listar_motores():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT * FROM motores")

    dados = cur.fetchall()

    conn.close()

    return dados
