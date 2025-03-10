import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os, sys
import time
import re

print('''
[ -1 ] - baixar Todos      
[ 0 ] - baixar protocolados      
[ 1 ] - baixar definidos      
[ 2 ] - baixar finalizado      
[ 3 ] - baixar cancelado      
[ 4 ] - baixar interrompido      
''')

try:
    escolher_status = int(input('Digite o status do prospecto a baixar [-1, 0, 1, 2, 3, 4]: '))
    
except ValueError:
    print('Nao é inteiro')
    sys.exit(0)

# URL da página principal com as empresas
BASE_URL = "https://statusinvest.com.br/ipo/acoes"

# Cabeçalhos para simular um navegador (com mais informações)
headers = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/91.0.4472.124 Safari/537.36"),

}

status = {
    '-1': '0',
    '0': '0',
    '1': '1',
    '2': '2',
    '3': '3',
    '4': '4'
}

status = status[str(escolher_status)]

if status == '-1':
    download_folder = "./data/Todos/"
    
elif status == '0':
    download_folder = "./data/protocolados/"

elif status == '1':
    download_folder = "./data/definidos/"
    
elif status == '2':
    download_folder = "./data/finalizado/"
    
elif status == '3':
    download_folder = "./data/cancelado/"
    
else:    
    download_folder = "./data/interrompido/"

# Diretório para salvar os PDFs
os.makedirs(download_folder, exist_ok=True)

# Função para baixar o PDF
def download_pdf(pdf_url, filename):
    try:
        # Faz a requisição para o PDF
        pdf_response = requests.get(pdf_url, headers=headers)
        pdf_response.raise_for_status()  # Verifica se houve erro na requisição
        with open(filename, 'wb') as pdf_file:
            pdf_file.write(pdf_response.content)  # Salva o conteúdo como PDF
        print(f"  PDF baixado com sucesso: {filename}")
    except requests.exceptions.RequestException as e:
        print(f"  Erro ao baixar o PDF: {e}")

# Função para acessar a página da empresa com tentativa em caso de erro 429
def acessar_pagina_empresa(url):
    attempts = 3  # Tentativas de acesso
    for attempt in range(attempts):
        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            print(f"  Erro 429 detectado. Tentando novamente após 5 segundos... (Tentativa {attempt + 1} de {attempts})")
            time.sleep(5)  # Espera 5 segundos antes de tentar novamente
        elif response.status_code == 200:
            return response
        else:
            print(f"  Erro ao acessar a página da empresa: {response.status_code}")
            return None
    return None

# 1. Obter a página principal e extrair os blocos de empresas com status selecionado
response = requests.get(BASE_URL, headers=headers)
if response.status_code != 200:
    print(f"Erro ao carregar a página principal: {response.status_code}")
    exit()

soup = BeautifulSoup(response.text, 'html.parser')

# Filtra os blocos das empresas com o status selecionado
company_divs = soup.find_all("div", attrs={"data-status": f"{status}"})

# Extrai os links de cada empresa
company_links = set()
for div in company_divs:
    a_tag = div.find("a", href=True)
    if a_tag:
        company_links.add(a_tag["href"])

print("Links das empresas encontrados:")
for comp_link in company_links:
    full_company_link = comp_link if comp_link.startswith("http") else urljoin(BASE_URL, comp_link)
    print(full_company_link)

print("\nAgora, vamos obter o link de PDF para cada empresa:")

# 2. Para cada empresa, acessar sua página e procurar o link para o PDF
for comp_link in company_links:
    full_company_link = comp_link if comp_link.startswith("http") else urljoin(BASE_URL, comp_link)
    print(f"\nEmpresa: {full_company_link}")

    comp_response = acessar_pagina_empresa(full_company_link)
    if comp_response is None:
        continue

    comp_soup = BeautifulSoup(comp_response.text, 'html.parser')
    
    # Procura por todos os links que terminam com .pdf usando expressão regular
    pdf_link_tags = comp_soup.find_all('a', href=lambda href: href and re.search(r'\.pdf$', href.lower()))
    
    if not pdf_link_tags:
        print("  Nenhum link de PDF encontrado nesta empresa.")
        continue

    # Para cada link de PDF encontrado, resolve o link relativo e tenta baixar
    for pdf_tag in pdf_link_tags:
        pdf_url = pdf_tag['href']
        
        # Resolver links relativos
        pdf_url = urljoin(full_company_link, pdf_url)
        
        print(f"  Link de PDF encontrado: {pdf_url}")

        # Verifica se o link para o PDF é válido
        if re.search(r'\.pdf$', pdf_url.lower()):
            # Obtém o nome da empresa da URL e remove caracteres especiais
            company_name = full_company_link.split("/")[-1].replace("-", "_").replace(" ", "_")
            filename = os.path.join(download_folder, f"{company_name}_{pdf_url.split('/')[-1]}")
            download_pdf(pdf_url, filename)
    
    # Adiciona um delay entre as requisições
    time.sleep(2)  # Espera 2 segundos entre as requisições para as páginas das empresas