from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
import time
import os
import re

# Configurações
csv_file_path = r'H:\Meu Drive\Trabalhos\2023\projetos\UNIFOR\prosaude\robo_portaria\medicamentos.csv'
output_csv_path = r'H:\Meu Drive\Trabalhos\2023\projetos\UNIFOR\prosaude\robo_portaria\resultados.csv'
chrome_driver_path = r'C:\Users\wilgner\Downloads\chromedriver-win64\chromedriver.exe'
os.environ["PATH"] += os.pathsep + chrome_driver_path

# Função para extrair o número de registro ANVISA da página do Google
def extract_anvisa_number(search_result):
    anvisa_number = None
    for result in search_result:
        if 'ANVISA' in result.text:
            # Procurar por padrões de números de registro
            matches = re.findall(r'\d{9}', result.text)
            if matches:
                anvisa_number = matches[0]
                break
    return anvisa_number

# Função para verificar se o medicamento está registrado na ANVISA
def check_anvisa_registration(anvisa_number):
    # Inicializar o WebDriver do Selenium
    driver = webdriver.Chrome()
    
    try:
        # Montar a URL com o número de registro
        url = f'https://consultas.anvisa.gov.br/#/medicamentos/q/?numeroRegistro={anvisa_number}'
        
        # Tentar acessar a URL
        driver.get(url)
        
        # Aguardar um curto período de tempo para garantir que a página seja carregada
        time.sleep(3)
        
        # Verificar se a página contém a mensagem "Nenhum registro encontrado"
        if "Nenhum registro encontrado" in driver.page_source:
            return "Não"
        else:
            return "Sim"
    except Exception as e:
        print(f"Erro ao verificar registro na ANVISA: {e}")
        return "Erro"
    finally:
        # Fechar o WebDriver
        driver.quit()

# Inicializar o WebDriver do Selenium
driver = webdriver.Chrome()

# Carregar o arquivo CSV
df = pd.read_csv(csv_file_path)

# Lista para armazenar os resultados
results = []

count = 0

# Loop através dos medicamentos
for medicamento in df['NOME_MEDICAMENTO']:
    
    count = count + 1
    if count > 2:
        break
    # Pesquisar no Google
    driver.get(f'https://www.google.com/search?q={medicamento}+numero+registro+ANVISA')
    
    # Aguardar até que os resultados da pesquisa estejam disponíveis
    time.sleep(3)
    
    # Extrair o HTML da página
    page_source = driver.page_source
    
    # Extrair o número de registro ANVISA
    soup = BeautifulSoup(page_source, 'html.parser')
    search_results = soup.find_all(class_='g')
    anvisa_number = extract_anvisa_number(search_results)
    
    # Verificar se o número de registro é válido e se o medicamento está registrado na ANVISA
    if anvisa_number:
        registrado_na_anvisa = check_anvisa_registration(anvisa_number)
    else:
        registrado_na_anvisa = "Não"
    
    # Salvar o resultado
    results.append({'Medicamento': medicamento, 'Número de Registro ANVISA': anvisa_number, 'Registrado na ANVISA': registrado_na_anvisa})

# Fechar o WebDriver
driver.quit()

# Criar DataFrame com os resultados
result_df = pd.DataFrame(results)

# Salvar DataFrame em um arquivo CSV
result_df.to_csv(output_csv_path, index=False)
