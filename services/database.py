import sqlite3
import json
import os

DB = "data/motores.db"

os.makedirs("data", exist_ok=True)

def conectar():
    return sqlite3.connect(DB, check_same_thread=False)

# ================= TABELA =================

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

criar_tabela()

# ================= SALVAR =================

def salvar_motor(motor):

    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO motores (dados) VALUES (?)",
        (json.dumps(motor, ensure_ascii=False),)
    )

    conn.commit()
    conn.close()

# ================= LISTAR =================

def listar_motores():

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

# ================= ATUALIZAR =================

def atualizar_motor(id_motor, motor):

    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        "UPDATE motores SET dados=? WHERE id=?",
        (json.dumps(motor, ensure_ascii=False), id_motor)
    )

    conn.commit()
    conn.close()

# ================= EXCLUIR =================

def excluir_motor(id_motor):

    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM motores WHERE id=?",
        (id_motor,)
    )

    conn.commit()
    conn.close()
