import sqlite3
import os

FOLDER = "database"
DB_PATH = os.path.join(FOLDER, "motores.db")

# Garante que a pasta 'database' existe
if not os.path.exists(FOLDER):
    os.makedirs(FOLDER)

def conectar():
    # check_same_thread=False é importante para o Streamlit
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def criar_tabela():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS motores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        marca TEXT, modelo TEXT, carcaca TEXT, peso REAL,
        potencia REAL, unidade_potencia TEXT, tensao REAL,
        amperagem REAL, polos INTEGER, fator_potencia REAL,
        rpm INTEGER, ip TEXT, isolamento TEXT, fs REAL,
        refrigeracao TEXT, ligacao TEXT, desenho TEXT
    )
    """)
    conn.commit()
    conn.close()

# Chama a criação da tabela automaticamente
criar_tabela()

def salvar_motor(dados):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO motores (
        marca, modelo, carcaca, peso, potencia, unidade_potencia, 
        tensao, amperagem, polos, fator_potencia, rpm, ip, 
        isolamento, fs, refrigeracao, ligacao, desenho
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, dados)
    conn.commit()
    conn.close()

def buscar_motor(busca):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM motores
    WHERE marca LIKE ? OR modelo LIKE ?
    """, (f"%{busca}%", f"%{busca}%"))
    resultados = cursor.fetchall()
    conn.close()
    return resultados

def motor_existe(marca, modelo, potencia, tensao):
    conn = conectar()
    c = conn.cursor()
    c.execute("""
    SELECT * FROM motores
    WHERE marca=? AND modelo=? AND potencia=? AND tensao=?
    """, (marca, modelo, potencia, tensao))
    resultado = c.fetchone()
    conn.close()
    return resultado is not None # <--- CORRIGIDO AQUI
