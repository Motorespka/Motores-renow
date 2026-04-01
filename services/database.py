import sqlite3
import json
import os

DB = "data/motores.db"

# ================= GARANTE PASTA =================

os.makedirs("data", exist_ok=True)

# ================= CONEXÃO =================

def conectar():
    return sqlite3.connect(DB, check_same_thread=False)

# ================= CRIAR TABELA =================

def criar_tabela():

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS motores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dados TEXT
        )
    """)

    conn.commit()
    conn.close()

# ⚡ EXECUTA SEMPRE
criar_tabela()

# ================= SALVAR =================

def salvar_motor(motor):

    criar_tabela()  # 🔥 garantia absoluta

    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO motores (dados) VALUES (?)",
        (json.dumps(motor),)
    )

    conn.commit()
    conn.close()

# ================= LISTAR =================

def listar_motores():

    criar_tabela()

    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT id, dados FROM motores")

    resultados = cur.fetchall()
    conn.close()

    motores = []

    for id_motor, dados in resultados:
        motor = json.loads(dados)
        motor["id"] = id_motor
        motores.append(motor)

    return motores

# ================= EXCLUIR =================

def excluir_motor(id_motor):

    conn = conectar()
    cur = conn.cursor()

    cur.execute("DELETE FROM motores WHERE id=?", (id_motor,))

    conn.commit()
    conn.close()
