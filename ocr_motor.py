import sqlite3
import os

FOLDER = "database"
# Usamos abspath para garantir que o SQLite sempre encontre o arquivo, independente de onde o Streamlit é chamado
DB_PATH = os.path.abspath(os.path.join(FOLDER, "motores.db"))

# Garante que a pasta 'database' existe
if not os.path.exists(FOLDER):
    os.makedirs(FOLDER, exist_ok=True) # Adicionado exist_ok por segurança

def conectar():
    # check_same_thread=False é fundamental para evitar erros de concorrência no Streamlit
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def criar_tabela():
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS motores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marca TEXT, 
            modelo TEXT, 
            carcaca TEXT, 
            peso REAL,
            potencia REAL, 
            unidade_potencia TEXT, 
            tensao REAL,
            amperagem REAL, 
            polos INTEGER, 
            fator_potencia REAL,
            rpm INTEGER, 
            ip TEXT, 
            isolamento TEXT, 
            fs REAL,
            refrigeracao TEXT, 
            ligacao TEXT, 
            desenho TEXT
        )
        """)
        conn.commit()
    finally:
        conn.close()

# Chama a criação da tabela automaticamente ao importar o arquivo
criar_tabela()

def salvar_motor(dados):
    conn = conectar()
    try:
        cursor = conn.cursor()
        # Adicionado tratamento de erro caso a tupla 'dados' venha com tamanho errado
        cursor.execute("""
        INSERT INTO motores (
            marca, modelo, carcaca, peso, potencia, unidade_potencia, 
            tensao, amperagem, polos, fator_potencia, rpm, ip, 
            isolamento, fs, refrigeracao, ligacao, desenho
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, dados)
        conn.commit()
    except Exception as e:
        print(f"Erro ao salvar motor: {e}")
        raise e # Repassa o erro para o Streamlit exibir o alerta
    finally:
        conn.close()

def buscar_motor(busca):
    conn = conectar()
    try:
        cursor = conn.cursor()
        # Busca insensível a maiúsculas/minúsculas
        cursor.execute("""
        SELECT * FROM motores
        WHERE marca LIKE ? OR modelo LIKE ?
        """, (f"%{busca}%", f"%{busca}%"))
        resultados = cursor.fetchall()
        return resultados
    finally:
        conn.close()

def motor_existe(marca, modelo, potencia, tensao):
    conn = conectar()
    try:
        c = conn.cursor()
        c.execute("""
        SELECT 1 FROM motores
        WHERE marca=? AND modelo=? AND potencia=? AND tensao=?
        LIMIT 1
        """, (marca, modelo, potencia, tensao))
        resultado = c.fetchone()
        return resultado is not None
    finally:
        conn.close()
