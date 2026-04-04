import os
import sqlite3
import json
import requests
import easyocr
import pdfplumber
from PIL import Image
from pillow_heif import register_heif_opener

# 1. PREPARAÇÃO PARA FOTOS DE CELULAR (.HEIC)
register_heif_opener()

# --- CONFIGURAÇÕES ---
# Pegue sua chave grátis em: https://openrouter.ai/keys
CHAVE_API_OPENROUTER = "SUA_CHAVE_AQUI"
PASTA_DOS_MOTORES = "Caminho/Para/Sua/Pasta/De/Arquivos"

# Inicializa o Leitor de Imagens (Português)
print("⚙️ Carregando visão computacional...")
reader = easyocr.Reader(['pt'])

# 2. CRIAÇÃO DO BANCO DE DADOS
def iniciar_banco():
    conn = sqlite3.connect('banco_site_motores.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS motores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_arquivo TEXT,
            marca TEXT,
            potencia TEXT,
            polos TEXT,
            ranhuras TEXT,
            principal_fio TEXT,
            principal_passo TEXT,
            auxiliar_fio TEXT,
            auxiliar_passo TEXT,
            texto_completo TEXT
        )
    ''')
    conn.commit()
    return conn

# 3. LEITURA DE TEXTO (OCR E PDF)
def extrair_texto(caminho):
    ext = caminho.lower().split('.')[-1]
    texto = ""
    try:
        if ext in ['jpg', 'jpeg', 'png', 'heic']:
            # Lendo imagem/foto
            resultado = reader.readtext(caminho, detail=0)
            texto = " ".join(resultado)
        elif ext == 'pdf':
            # Lendo PDF
            with pdfplumber.open(caminho) as pdf:
                for pagina in pdf.pages:
                    texto += (pagina.extract_text() or "") + " "
        elif ext == 'txt':
            with open(caminho, 'r', encoding='utf-8', errors='ignore') as f:
                texto = f.read()
    except Exception as e:
        print(f"❌ Erro ao ler {caminho}: {e}")
    return texto

# 4. INTELIGÊNCIA ARTIFICIAL (ORGANIZAÇÃO)
def organizar_com_ia(texto_bruto):
    if not texto_bruto.strip(): return None

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {CHAVE_API_OPENROUTER}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    Você é um especialista em rebobinagem de motores. 
    Extraia os dados técnicos deste texto e responda APENAS em JSON.
    Campos: marca, potencia, polos, ranhuras, principal_fio, principal_passo, auxiliar_fio, auxiliar_passo.
    Texto: {texto_bruto[:1500]}
    """

    payload = {
        "model": "meta-llama/llama-3-8b-instruct:free",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        res = response.json()
        conteudo = res['choices'][0]['message']['content']
        # Limpando a resposta para pegar só o JSON
        json_str = conteudo[conteudo.find("{"):conteudo.rfind("}")+1]
        return json.loads(json_str)
    except:
        return None

# 5. EXECUÇÃO PRINCIPAL
def processar_tudo():
    conn = iniciar_banco()
    cursor = conn.cursor()
    
    print(f"🚀 Iniciando busca em: {PASTA_DOS_MOTORES}")
    
    for raiz, _, arquivos in os.walk(PASTA_DOS_MOTORES):
        for arq in arquivos:
            caminho_completo = os.path.join(raiz, arq)
            print(f"📂 Lendo: {arq}")
            
            # Passo A: Extrair texto da foto ou arquivo
            texto = extrair_texto(caminho_completo)
            
            # Passo B: IA entende o que é Fio, Passo, etc.
            dados = organizar_com_ia(texto)
            
            if dados:
                # Passo C: Salva no Banco de Dados
                cursor.execute('''
                    INSERT INTO motores (
                        nome_arquivo, marca, potencia, polos, ranhuras, 
                        principal_fio, principal_passo, auxiliar_fio, auxiliar_passo, texto_completo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    arq, dados.get('marca'), dados.get('potencia'), 
                    dados.get('polos'), dados.get('ranhuras'),
                    dados.get('principal_fio'), dados.get('principal_passo'),
                    dados.get('auxiliar_fio'), dados.get('auxiliar_passo'),
                    texto[:500]
                ))
                conn.commit()
                print(f"✅ Dados de {arq} salvos!")

    conn.close()
    print("\n🏁 PROCESSO CONCLUÍDO! Banco de dados 'banco_site_motores.db' criado.")

if __name__ == "__main__":
    processar_tudo()
