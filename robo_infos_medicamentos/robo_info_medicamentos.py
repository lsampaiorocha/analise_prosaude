from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
import time
import os
import re

# Configurações
csv_file_path = r'C:\Users\wilgner\Desktop\ELASTICSEARCH\PROSAUDE\medicamentos - Copia.csv'
output_csv_path = r'C:\Users\wilgner\Desktop\ELASTICSEARCH\PROSAUDE\resultado-medicamentos.csv'
chrome_driver_path = r'C:\Users\wilgner\Downloads\chromedriver-win64\chromedriver.exe'
os.environ["PATH"] += os.pathsep + chrome_driver_path

# Inicializar o WebDriver do Selenium
driver = webdriver.Chrome()

# Função para extrair número do processo a partir da página de detalhes do medicamento
def extract_process_number(page_source):
    process_number = None
    soup = BeautifulSoup(page_source, 'html.parser')
    process_tag = soup.find('td', class_='text-center col-sm-2 ng-binding')
    if process_tag:
        process_number = process_tag.text.strip()
    return process_number

# Função para extrair nome do princípio ativo e nome comercial a partir da página de detalhes do medicamento
def extract_active_principle_and_commercial_name(page_source):
    active_principle = None
    commercial_name = None
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Extrair nome do princípio ativo
    active_principle_tag = soup.find('td', class_='text-center col-sm-1 ng-binding', attrs={'ng-show': 'tipoProduto == 1'})
    if active_principle_tag:
        active_principle = active_principle_tag.text.strip()
    
    # Extrair nome comercial
    commercial_name_tag = soup.find('td', class_='col-xs-2 ng-binding', attrs={'ng-click': 'detail(produto)'})
    if commercial_name_tag:
        commercial_name = commercial_name_tag.text.strip()
    
    return active_principle, commercial_name

# Função para extrair a situação do medicamento (Válido ou Caduco/Cancelado)
def extract_medication_status(page_source):
    status = None
    soup = BeautifulSoup(page_source, 'html.parser')
    status_tag = soup.find('td', class_='text-center col-sm-1 ng-binding', string=re.compile(r'(Válido|Caduco/Cancelado)'))
    if status_tag:
        status = status_tag.text.strip()
    return status

# Função para verificar se o medicamento está registrado na ANVISA
def check_anvisa_registration(anvisa_number):
    try:
        # Montar a URL da página de detalhes do medicamento na ANVISA
        process_url = f'https://consultas.anvisa.gov.br/#/medicamentos/q/?numeroRegistro={anvisa_number}'
        
        # Tentar acessar a URL
        driver.get(process_url)
        
        # Aguardar um curto período de tempo para garantir que a página seja carregada
        time.sleep(6)
        
        # Extrair nome do princípio ativo, nome comercial e situação do medicamento
        active_principle, commercial_name = extract_active_principle_and_commercial_name(driver.page_source)
        status = extract_medication_status(driver.page_source)
        
        # Extrair número do processo
        process_number = extract_process_number(driver.page_source)
        
        return process_number, active_principle, commercial_name, status
    except Exception as e:
        print(f"Erro ao verificar registro na ANVISA: {e}")
        return None, None, None, None



# Carregar o arquivo CSV
df = pd.read_csv(csv_file_path, encoding='latin1')

# Lista para armazenar os resultados
results = []

# Loop através dos medicamentos
for medication_name in df['NOME_MEDICAMENTO']:
    # Verificar se a entrada não está vazia
    if medication_name.strip():  # Verifica se a string não está vazia após remoção dos espaços em branco
        # Pesquisar no Google apenas pelo primeiro resultado
        driver.get(f'https://www.google.com/search?q={medication_name}+numero+registro+ANVISA&num=1')
        
        # Aguardar até que os resultados da pesquisa estejam disponíveis
        time.sleep(6)
        
        # Extrair o HTML da página
        page_source = driver.page_source
        
        # Extrair o número de registro ANVISA
        soup = BeautifulSoup(page_source, 'html.parser')
        search_results = soup.find_all(class_='g')
        anvisa_number = None
        for result in search_results:
            if 'ANVISA' in result.text:
                # Procurar por padrões de números de registro
                matches = re.findall(r'(\d{9})', result.text)
                if matches:
                    anvisa_number = matches[0]
                    break
        
        # Verificar se o número de registro é válido e se o medicamento está registrado na ANVISA
        if anvisa_number:
            process_number, active_principle, commercial_name, status = check_anvisa_registration(anvisa_number)
            if process_number:
                # Verificar se todos os campos necessários estão preenchidos
                if active_principle or commercial_name:
                    registered_in_anvisa = "Sim"
                else:
                    registered_in_anvisa = "Não"
            else:
                registered_in_anvisa = "Não"
        else:
            process_number = None
            active_principle = None
            commercial_name = None
            status = None
            registered_in_anvisa = "Não"
    else:
        # Entrada vazia, pular para o próximo medicamento
        continue
    
    # Salvar o resultado
    results.append({'Medicamento': medication_name, 
                    'Nome Comercial': commercial_name, 
                    'Nome do Princípio Ativo': active_principle,
                    'Número de Registro ANVISA': anvisa_number, 
                    'Número do Processo ANVISA': process_number, 
                    'Registrado na ANVISA': registered_in_anvisa,
                    'Situação': status})

# Fechar o WebDriver
driver.quit()

# Criar DataFrame com os resultados
result_df = pd.DataFrame(results)

# Salvar DataFrame em um arquivo CSV
result_df.to_csv(output_csv_path, index=False)
