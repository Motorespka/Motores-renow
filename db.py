import sqlite3
import os

# 1. Corrigido para 'database' (um 's' apenas) 
FOLDER = "database"
DB_PATH = os.path.join(FOLDER, "motores.db")

if not os.path.exists(FOLDER):
    os.makedirs(FOLDER)

def conectar():
    return sqlite3.connect(DB_PATH)

def criar_tabela():
    conn = conectar()
    cursor = conn.cursor()
    # Criação da tabela conforme os campos do cadastro 
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

def inserir_motor(dados):
    """ 'dados' deve ser uma tupla com 17 elementos  """
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
    # Busca por marca ou modelo usando LIKE 
    cursor.execute("""
    SELECT * FROM motores
    WHERE marca LIKE ? OR modelo LIKE ?
    """, (f"%{busca}%", f"%{busca}%"))
    resultados = cursor.fetchall()
    conn.close()
    return resultados

def motor_existe(marca, modelo, potencia, tensao):
    """ Corrigido: Agora recebe argumentos individuais em vez de dict/tupla  """
    conn = conectar()
    c = conn.cursor()
    c.execute("""
    SELECT * FROM motores
    WHERE marca=? AND modelo=? AND potencia=? AND tensao=?
    """, (marca, modelo, potencia, tensao))
    resultado = c.fetchone()
    conn.close()
    return resultado is not None