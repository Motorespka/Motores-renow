import sqlite3
from pathlib import Path

DB_PATH = Path("data/motores.db")
DB_PATH.parent.mkdir(exist_ok=True)  # garante que a pasta data exista

# =============================
# CRIAR TABELA SE NÃO EXISTIR
# =============================
def criar_tabela():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS motores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marca TEXT,
            modelo TEXT,
            potencia TEXT,
            tensao TEXT,
            corrente TEXT,
            rpm TEXT,
            frequencia TEXT,
            fp TEXT,
            carcaca TEXT,
            ip TEXT,
            isolacao TEXT,
            regime TEXT,
            rolamento_dianteiro TEXT,
            rolamento_traseiro TEXT,
            peso TEXT,
            diametro_eixo TEXT,
            comprimento_pacote TEXT,
            numero_ranhuras TEXT,
            ligacao TEXT,
            fabricacao TEXT,
            original TEXT
        )
    """)
    conn.commit()
    conn.close()

# Chama a função automaticamente para garantir que a tabela exista
criar_tabela()

# =============================
# INSERIR MOTOR
# =============================
def salvar_motor(motor: dict):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    campos = ", ".join(motor.keys())
    placeholders = ", ".join("?" for _ in motor)
    valores = list(motor.values())
    cur.execute(f"INSERT INTO motores ({campos}) VALUES ({placeholders})", valores)
    conn.commit()
    conn.close()

# =============================
# LISTAR MOTORES
# =============================
def listar_motores():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM motores")
    colunas = [desc[0] for desc in cur.description]
    resultados = [dict(zip(colunas, row)) for row in cur.fetchall()]
    conn.close()
    return resultados
