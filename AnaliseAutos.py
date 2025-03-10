import fitz  # PyMuPDF
import PyPDF2
import re
import os
import pdfplumber
import csv

from datetime import datetime, timedelta




#Função principal que busca os nomes de documentos de interesse na lista interests e tenta encontrar o id de documentos na lista
#caso existam
def encontra_id_documento_analise(pdf_path,document_info,interests):
    # Inicializa varávais para checar se o documento correto é realmente o selecionado
    # pelo robô
    analysed_ids = []
    
    # Captura os andamentos de interesse para a aplicação de portaria
    # dado a lista de andamentos do processo
    
    try:
        tipos_encontrados = CheckTypesOfInterest(document_info, interests)
    except Exception as e:
        print(f"Erro ao encontrar o documento para analise: {e}")
        raise RuntimeError(f"Erro ao encontrar o documento para analise: {e}")

    if not tipos_encontrados:
        print("Nenhum tipo de interesse encontrado no documento fornecido.")
        raise RuntimeError(f"Erro ao encontrar o documento para analise: Nenhum tipo de interesse encontrado no documento fornecido.")
    
    #print(tipos_encontrados)
    # Seleciona o último ID de interesse para a análise de Aplicação 
    # da portaaria  01/2017
   
    try:
        selecao = select_id_to_analyze(tipos_encontrados,analysed_ids)
    except Exception as e:
        print(f"Erro ao encontrar o documento para analise: {e}")
        raise RuntimeError(f"Erro ao encontrar o documento para analise: {e}")
    
    if selecao is not None:
        id_selecionado,documento,tipo = selecao 
        # Faz uma série de Checagens para validar que o documento selecionado é realmente o que o Robô
        # necessita analisar
        #id_revisto =  CheckPDFDocument(pdf_path,id_selecionado,tipo,documento,tipos_encontrados,contagem_peticoes,analysed_ids)
        #print(f"Id Documento Selecionado: {id_revisto}")
        #return id_revisto
        return id_selecionado
    else:
        return None



def extract_pages_to_check(pdf_path):
    pdf_document = fitz.open(pdf_path)
    pages_to_check = []

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text = page.get_text("text")

        # Verifica se a página tem o padrão "Num. \d{8} - Pág. \d+"
        if not re.search(r"Num\. \d{8} - Pág\. \d+", text):
            pages_to_check.append(page_num)

    pdf_document.close()

    return pages_to_check


def extract_document_info_from_pages(pdf_path, pages_to_check):
    pdf_document = pdfplumber.open(pdf_path)
    document_info = []

    for page_num in pages_to_check:

        page = pdf_document.pages[page_num]
        
        tables = page.extract_tables()
        
        for T in tables:
            for table in T:
                if(None in table):
                    table.remove(None)
                if(type(table[0]) == str):
                    if(table[0].isnumeric() == False):
                        continue
                else:
                    i=0
                    while(type(table[i])!=str):
                        i+=1
                    last_entry = document_info.pop()
                    document_info.append({
                        "id_doc": last_entry["id_doc"],
                        "dt_assinatura": last_entry["dt_assinatura"],
                        "nome": last_entry["nome"] + table[i],
                        "tipo": last_entry["tipo"]
                    })
                    continue
                try:
                    id_doc = table[0]
                    data_assinatura = table[1].replace('\n', ' ')
                    documento = table[2].replace('\n', ' ')
                    tipo = table[3]
                    document_info.append({
                        "id_doc": id_doc,
                        "dt_assinatura": data_assinatura,
                        "nome": documento,
                        "tipo": tipo
                    })
                except Exception as e:
                        print(f"Erro ao processar")
                        continue 
    #save_lists_to_csv(document_info,append= True)                    
    pdf_document.close()

    return document_info



# Retorna uma lista com as informações de documentos que casam com os tipos de interesse (interests)
def CheckTypesOfInterest(document_info, interests):
    found_types = []
    peticao_docs = []

    # Define o período máximo permitido (últimos 60 dias)
    periodo = datetime.now() - timedelta(days=60)
    
    
    # Mapeamento de caracteres acentuados e suas versões sem acento
    accent_map = str.maketrans(
        "áàãâäéèêëíìîïóòõôöúùûüç",
        "aaaaaeeeeiiiiooooouuuuc"
    )
    
    # Gera expressões regulares que consideram a ausência de acentos
    interest_patterns = [
        re.compile(fr"\b{re.escape(interesse).translate(accent_map)}\b", re.IGNORECASE) 
        for interesse in interests
    ]

    for info in document_info:
        # Garantir que a tupla tem o formato esperado
        if not isinstance(info, dict):
            raise ValueError(f"Entrada inválida em document_info: {info}. Esperado um dicionário.")

        id_doc = info.get("id_doc")
        data_assinatura_str = info.get("dt_assinatura")
        documento = info.get("nome")
        tipo = info.get("tipo")

        # Validação básica dos campos obrigatórios
        if id_doc is None or data_assinatura_str is None or documento is None or tipo is None:
            raise ValueError(f"Campos ausentes no dicionário: {info}")

        """
        # Converte a data de assinatura para datetime (se possível)
        try:
            data_assinatura = datetime.strptime(data_assinatura_str, "%d/%m/%Y")  # Formato esperado: DD/MM/YYYY
        except ValueError:
            print(f"Aviso: Data inválida no documento {id_doc} - {data_assinatura_str}")
            continue  # Ignora documentos com datas inválidas

        """
        
        # Converte a data de assinatura para datetime (se possível)
        # Usa a função parse_data_assinatura para tratar diferentes formatos de data
        data_assinatura = parse_data_assinatura(data_assinatura_str)

        if data_assinatura is None:
            print(f"Erro: Data inválida no documento {id_doc} - {data_assinatura_str}")
            raise ValueError(f"Erro: Data inválida no documento {id_doc} - {data_assinatura_str}")

        # Filtra apenas documentos assinados nos últimos 2 meses
        if data_assinatura < periodo:
            continue  # Ignora documentos antigos

        # Remove acentos dos campos a serem comparados
        documento_normalizado = documento.translate(accent_map)
        tipo_normalizado = tipo.translate(accent_map)
        
        #verifica se o padrão regex está presente no texto
        for pattern in interest_patterns:
            if pattern.search(tipo_normalizado) or pattern.search(documento_normalizado):
                found_types.append({
                    "id_doc": int(id_doc),
                    "dt_assinatura": data_assinatura_str,
                    "nome": documento,
                    "tipo": tipo
                })

        # Padrão para "petição" sem acentos
        if re.search(r"\bpeticao\b", documento_normalizado, re.IGNORECASE) or \
           re.search(r"\bpeticao\b", tipo_normalizado, re.IGNORECASE):
            peticao_docs.append({
                "id_doc": int(id_doc),
                "dt_assinatura": data_assinatura_str,
                "nome": documento,
                "tipo": tipo
            })

        """
        for interesse in interests:
            if interesse.lower() in tipo.lower() or interesse.lower() in documento.lower():
                # Modificado Nathanael 09/2024
                found_types.append({
                    "id_doc": int(id_doc),
                    "dt_assinatura": data_assinatura_str,
                    "nome": documento,
                    "tipo": tipo
                })
        

        # Sempre inclui petições, mas agora só se forem recentes
        if "petição" in documento.lower() or "petição" in tipo.lower():
            peticao_docs.append({
                "id_doc": int(id_doc),
                "dt_assinatura": data_assinatura_str,
                "nome": documento,
                "tipo": tipo
            })
        """

    # Caso tenha encontrado algum documento que atende os criterios
    if found_types:
        return found_types 

    return []  # Retorna lista vazia se nenhum documento atender aos critérios


#Faz o tratamento correto das datas
def parse_data_assinatura(data_assinatura_str):
    """Tenta converter a string de data para um objeto datetime em vários formatos possíveis."""
    
    # Normaliza a string para remover quebras de linha e espaços desnecessários
    data_assinatura_str = " ".join(data_assinatura_str.split()).strip()
    
    # Define os formatos aceitos, incluindo data e hora
    formatos_aceitos = [
        "%d/%m/%Y %H:%M",  # Formato completo: 20/07/2023 13:53
        "%d/%m/%Y",         # Apenas data: 20/07/2023
        "%Y-%m-%d %H:%M",   # Formato ISO com hora: 2023-07-20 13:53
        "%Y-%m-%d",         # Formato ISO só data: 2023-07-20
        "%d-%m-%Y %H:%M",   # Alternativa com traços: 20-07-2023 13:53
        "%d-%m-%Y",         # Data apenas com traços: 20-07-2023
    ]
    
    for formato in formatos_aceitos:
        try:
            return datetime.strptime(data_assinatura_str, formato)
        except ValueError:
            continue
    
    print(f"Aviso: Data e hora em formato desconhecido: {data_assinatura_str}")
    return None


#Retorna uma lista com as informações de documentos que casam com os tipos de interesse (interests)
def CheckTypesOfInterest_old(document_info, interests, forca_peticao):
    found_types = []
    peticao_docs = []

    for info in document_info:
        # Garantir que a tupla tem o formato esperado
        if not isinstance(info, dict):
            raise ValueError(f"Entrada inválida em document_info: {info}. Esperado um dicionário.")

        id_doc = info.get("id_doc")
        data_assinatura = info.get("dt_assinatura")
        documento = info.get("nome")
        tipo = info.get("tipo")

        if id_doc is None or data_assinatura is None or documento is None or tipo is None:
            raise ValueError(f"Campos ausentes no dicionário: {info}")

        for interesse in interests:
            if interesse.lower() in tipo.lower() or interesse.lower() in documento.lower():
                # Modificado Nathanael 09/2024
                found_types.append({
                    "id_doc": int(id_doc),
                    "dt_assinatura": data_assinatura,
                    "nome": documento,
                    "tipo": tipo
                })

            #Sempre inclui petições. Vale a pena manter assim? (Leo)
            if "petição" in documento.lower() or "petição" in tipo.lower():
                peticao_docs.append({
                    "id_doc": int(id_doc),
                    "dt_assinatura": data_assinatura,
                    "nome": documento,
                    "tipo": tipo
                })

    # Modificado Nathanael 09/2024
    if found_types and forca_peticao == 0:
        # Resultado pode ser retornado diretamente
        return found_types

    # Se necessário, retornar também peticao_docs ou outro comportamento padrão
    #return {"found_types": found_types, "peticao_docs": peticao_docs}



def check_pdf_in_folder(folder_path, interests,forca_peticao):
    tipos_encontrados = check_document_types(folder_path, interests,forca_peticao)

    if not tipos_encontrados:
        print(f"Nenhum tipo de interesse encontrado no processo {folder_path}.")
    return tipos_encontrados


#Verifica algumas expressões que caracterizam uma petição
def search_by_expression(pdf_path):
    # Abre o arquivo PDF
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        num_pages = len(reader.pages)

        id_pattern = r"Num\. (\d+) - Pág\."
           
        pedidos_pattern = re.compile(r"Dos\s+Pedidos", re.IGNORECASE)
        requerimentos_pattern = re.compile(r"Dos\s+Requerimentos", re.IGNORECASE)

        for i in range(num_pages):
            page = reader.pages[i]
            text = page.extract_text()  

            if text:
                if pedidos_pattern.search(text) or requerimentos_pattern.search(text):

                    match = re.search(id_pattern, text)
                    if match:
                        document_id = match.group(1)  # Captura o número do ID
                        return document_id

    return None


#Seleciona o id do último documento que segue os critérios de interesse
def select_id_to_analyze(tipos_encontrados, analysed_ids):
    lista_selecao = [item for item in tipos_encontrados if item not in analysed_ids]
    if not lista_selecao:
        return None  
    documento_selecionado = lista_selecao[0]
    
    if not all(key in documento_selecionado for key in ["id_doc", "nome", "tipo"]):
        raise RuntimeError(f"Campos incompletos para o documento: {documento_selecionado}")
    

    id_selecionado = documento_selecionado["id_doc"]
    documento = documento_selecionado["nome"]
    tipo = documento_selecionado["tipo"]
    analysed_ids.append(documento_selecionado)
    return id_selecionado, documento, tipo



def check_document_types(pdf_path, interests,forca_peticao):
    pages_to_check = extract_pages_to_check(pdf_path)
    document_info = extract_document_info_from_pages(pdf_path, pages_to_check)
    found_types = []
    # Modificado Nathanael 09/2024
    peticao_docs = []
    for info in document_info:
        id_doc, data_assinatura, documento, tipo = info
        for interesse in interests:
            if interesse.lower() in tipo.lower() or interesse.lower() in documento.lower():
                # Modificado Nathanael 09/2024
                found_types.append((int(id_doc), data_assinatura, documento, interesse))
                
                
            if "petição" in documento.lower() or "petição" in tipo.lower():
                peticao_docs.append((int(id_doc), data_assinatura, documento, tipo))
    #Modificado Nathanael 09/2024
    if found_types and forca_peticao == 0:
        #resultado =  filter_by_date(found_types)
        resultado = found_types
        return resultado
    else:
        print('Forçou Petição')
        #resultado =  filter_by_date(peticao_docs)
        resultado = peticao_docs
        menor_peticao_id = min(resultado, key=lambda x: x[0])[0]
        menor_peticao_docs = [doc for doc in resultado if doc[0] == menor_peticao_id]
        return menor_peticao_docs



# Devo fazer uma função quase igual a extract_document_by_id, porém ela não deve me retonar um documento baixado 
# Ela deve me retornar o id
# Já apaguei as variáveis necessárias para baixar os documentos 
def CheckPDFDocument(pdf_path, id_selecionado, tipo, documento, tipos_encontrados, contagem_peticoes, analysed_ids):
    pdf_document = fitz.open(pdf_path)
    pages_to_extract = []

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text = page.get_text()
        if f"Num. {id_selecionado} - Pág." in text:
            pages_to_extract.append(page_num)

    new_pdf = fitz.open()
    text_length = 0 
    full_text = ""

    for page_num in pages_to_extract:
        new_pdf.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)
        page = pdf_document.load_page(page_num)
        text = page.get_text()
        full_text += text
        text_length += len(text)

    if contagem_peticoes >= 2:
        print('Nenhum documento relevante foi encontrado')
        return id_selecionado

    if text_length < 3000 and ("petição" in tipo.lower() or "petição" in documento.lower()):
        contagem_peticoes += 1
        id_selecionado = search_by_expression(pdf_path)
        analysed_ids.append(id_selecionado)
        return CheckPDFDocument(pdf_path, id_selecionado, tipo, documento, tipos_encontrados, contagem_peticoes, analysed_ids)

    if "decisão" in tipo.lower() or "decisão" in documento.lower():
        deferimento = re.compile(r"Defiro|Indefiro|Deferimento|Concedo|Deferir|Acolho", re.IGNORECASE)
        tutela = re.compile(r"Tutela|Urgência", re.IGNORECASE)

        if not deferimento.search(full_text) or not tutela.search(full_text):
            try:
                id_selecionado, documento, tipo = select_id_to_analyze(tipos_encontrados, analysed_ids)
            except Exception as e:
                return None

            if id_selecionado:
                return CheckPDFDocument(pdf_path, id_selecionado, tipo, documento, tipos_encontrados, contagem_peticoes, analysed_ids)
            else:
                forca_peticao = 1
                interesses = ["Petição Inicial", "Decisão", "Sentença", "Interlocutória"]
                tipos_encontrados = check_pdf_in_folder(pdf_path, interesses, forca_peticao)
                id_selecionado, _, documento, tipo = tipos_encontrados[0]
                return CheckPDFDocument(pdf_path, id_selecionado, tipo, documento, tipos_encontrados, contagem_peticoes, analysed_ids)

    return id_selecionado
