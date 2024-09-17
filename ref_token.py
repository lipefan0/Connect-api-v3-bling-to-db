import os
import requests
import pyodbc
import base64
from dotenv import load_dotenv

def refresh_token():
    # Carrega as variáveis de ambiente
    load_dotenv('.env')

    db_sql_server = os.environ.get('DATABASE_URL_ODBC') # Utilizo o ODBC para conectar ao SQL Server, mas pode ser utilizado qualquer outro método de conexão
    print("Conectando a base de dados")
    conn_str = str(db_sql_server)
    conn = pyodbc.connect(conn_str) # Utilizo a biblioteca pyodbc para conectar ao SQL Server, mas pode ser utilizado qualquer outro método de conexão
    cursor = conn.cursor()

    try:
        document_id = 1 # id da linha que contém o refresh token
        cursor.execute(f"SELECT ClientId, ClientSecret, TokenRefresh FROM Token WHERE id = {document_id}")
        row = cursor.fetchone()

        if not row:
            print("Token não encontrado")
            return
        
        clientId, clientSecret, refToken = row

        if not clientId or not clientSecret or not refToken:
            print("Credenciais ou TokenRefresh ausentes no documento.")
            return
        
        credentials = base64.b64encode(f"{clientId}:{clientSecret}".encode()).decode() # faz um enconde das credenciais para base64

    except Exception as e:
        print(f"Falha ao conectar ou ler do SQL Database: {e}")
        return
    
    # Requisição para atualizar o token
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {credentials}'
    }

    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refToken
    }

    url = 'https://www.bling.com.br/Api/v3/oauth/token'
    response = requests.post(url, headers=headers, data=payload) # Utiliza a biblioteca requests para fazer a requisição

    if response.status_code == 200:
        data = response.json()
        cursor.execute("""
            UPDATE Token
            SET TokenAuth = ?, TokenRefresh = ? WHERE id = ? """,
            data['access_token'], data['refresh_token'], document_id)
        conn.commit() # Salva as alterações no banco de dados
        print("Token atualizado com sucesso")
    else:
        print(f"Erro ao atualizar o token: {response.status_code}")
    
    cursor.close()
    conn.close()
    
    if response.status_code == 400:
        print("Erro ao atualizar o token: 400 Bad Request")
        return
    
    if response.status_code == 401:
        print("Erro ao atualizar o token: 401 Unauthorized")
        return
    
    if response.status_code == 500:
        print("Erro ao atualizar o token: 500 Internal Server Error")
        return
    
if __name__ == '__main__':
    refresh_token()