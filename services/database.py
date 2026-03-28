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
            marca TEXT DEFAULT '',
            modelo TEXT DEFAULT '',
            potencia TEXT DEFAULT '',
            tensao TEXT DEFAULT '',
            corrente TEXT DEFAULT '',
            rpm TEXT DEFAULT '',
            frequencia TEXT DEFAULT '',
            fp TEXT DEFAULT '',
            carcaca TEXT DEFAULT '',
            ip TEXT DEFAULT '',
            isolacao TEXT DEFAULT '',
            regime TEXT DEFAULT '',
            rolamento_dianteiro TEXT DEFAULT '',
            rolamento_traseiro TEXT DEFAULT '',
            peso TEXT DEFAULT '',
            diametro_eixo TEXT DEFAULT '',
            comprimento_pacote TEXT DEFAULT '',
            numero_ranhuras TEXT DEFAULT '',
            ligacao TEXT DEFAULT '',
            fabricacao TEXT DEFAULT '',
            original TEXT DEFAULT 'Sim'
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
    """
    Salva um motor no banco de dados.
    Substitui valores None por string vazia para evitar problemas.
    """
    # Padronizar dados: None -> ''
    motor_limpo = {k: (v if v is not None else "") for k, v in motor.items()}

    # Garantir que todos os campos da tabela existam
    colunas_tabela = [
        "marca","modelo","potencia","tensao","corrente",
        "rpm","frequencia","fp","carcaca","ip",
        "isolacao","regime","rolamento_dianteiro",
        "rolamento_traseiro","peso","diametro_eixo",
        "comprimento_pacote","numero_ranhuras",
        "ligacao","fabricacao","original"
    ]
    for campo in colunas_tabela:
        if campo not in motor_limpo:
            motor_limpo[campo] = "" if campo != "original" else "Sim"

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    campos = ", ".join(motor_limpo.keys())
    placeholders = ", ".join("?" for _ in motor_limpo)
    valores = list(motor_limpo.values())
    cur.execute(f"INSERT INTO motores ({campos}) VALUES ({placeholders})", valores)
    conn.commit()
    conn.close()

# =============================
# LISTAR MOTORES
# =============================
def listar_motores():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM motores ORDER BY id DESC")  # os mais recentes primeiro
    colunas = [desc[0] for desc in cur.description]
    resultados = [dict(zip(colunas, row)) for row in cur.fetchall()]
    conn.close()
    return resultados
