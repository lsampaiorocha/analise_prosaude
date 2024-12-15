import fitz  # PyMuPDF
import PyPDF2
import re
import os
import pdfplumber
import csv
from datetime import datetime

def filter_by_date(lista_andamentos):
    lim_dias =120
    resultado = []
    hoje = datetime.now()
    
    for andamento in lista_andamentos :
        #print(andamento)
        data_str = andamento[1]
        data = datetime.strptime(data_str, '%d/%m/%Y')
        dif_dias = (hoje -data).days
        if dif_dias <= lim_dias:
            print(resultado)
            resultado.append(andamento)

    return resultado

def save_lists_to_csv(lists,append = False):
    file_name = 'andamentos'
    if not lists:
        raise ValueError("A lista fornecida está vazia.")
    mode = 'a' if append else 'w'
    try:
        with open(file_name, mode=mode, newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(lists)
        print(f"Arquivo salvo com sucesso.")
    except IOError as e:
        print(f"Erro ao salvar o arquivo CSV: {e}")


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
                    tempid_doc = document_info[-1][0]
                    tempdata_assinatura = document_info[-1][1]
                    tempdocumento = document_info[-1][2]+table[i]
                    temptipo = document_info[-1][3]
                    document_info.pop()
                    document_info.append((tempid_doc, tempdata_assinatura, tempdocumento, temptipo))
                    continue
                try:
                    id_doc = table[0]
                    data_assinatura = table[1].replace('\n',' ')
                    documento = table[2].replace('\n',' ')
                    tipo = table[3]
                    document_info.append((id_doc, data_assinatura, documento, tipo))
                except Exception as e:
                        print(f"Erro ao processar")
                        continue 
    #save_lists_to_csv(document_info,append= True)                    
    pdf_document.close()

    return document_info

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
    
def CheckTypesOfInterest(document_info,interests,forca_peticao):
    found_types = []
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


def check_pdf_in_folder(folder_path, interests,forca_peticao):
    tipos_encontrados = check_document_types(pdf_path, interests,forca_peticao)

    if tipos_encontrados:
        for tipo_encontrado in tipos_encontrados:
            id_doc, data_assinatura, documento, interesse = tipo_encontrado
    else:
        print(f"Nenhum tipo de interesse encontrado no processo {pdf_path}.")
    return tipos_encontrados


def CheckPdfInFolder(document_info, interests,forca_peticao):
    tipos_encontrados = CheckTypesOfInterest(document_info,interests,forca_peticao)
    if tipos_encontrados:
        for tipo_encontrado in tipos_encontrados:
            id_doc, data_assinatura, documento, interesse = tipo_encontrado
    else:
        print(f"Nenhum tipo de interesse encontrado no processo {pdf_path}.")
    return tipos_encontrados

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

#Modificado Nathanael 09/2024
def extract_document_by_id(pdf_path, document_id,tipo,documento, output_path, filename,tipos_encontrados,contagem_peticoes):
    pdf_document = fitz.open(pdf_path)
    pages_to_extract = []

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text = page.get_text()
        #print(text)

        if f"Num. {document_id} - Pág." in text:
            pages_to_extract.append(page_num)
            

    #print('Numero_Paginas_Extrai:',len(pages_to_extract))
    new_pdf = fitz.open()

    text_length = 0 
    full_text = ""
    for page_num in pages_to_extract:
        new_pdf.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)
        page = pdf_document.load_page(page_num)
        text = page.get_text()
        full_text += text
        text_length += len(text)

    if contagem_peticoes>=2:
        print('Nenhum documento relevante foi encontrado')
        return

   #print('Tamanho:',text_length)
    if text_length < 3000 and ("petição" in tipo.lower() or "petição" in documento.lower()) and contagem_peticoes<2 :
        print('Menor que 3000')
        contagem_peticoes +=1
        document_id = search_by_expression(pdf_path)
        extract_document_by_id(pdf_path, document_id,tipo,documento, output_path, filename,tipos_encontrados,contagem_peticoes)
        return
    #Caso da decisão:Passa por aqui , vai checar se possui as palavras escohidas, caso não possua, atualiza
    # a lista de ids , passa novamente para capturar o novo id a ser analizado e volta pro extract documento
    
    if ("decisão" in tipo.lower() or "decisão" in documento.lower() or "decisões" in documento.lower() or "decisões" in tipo.lower()):
       
               
        deferimento = re.compile(r"Defiro|Indefiro|Deferimento|Concedo|Deferir|Acolho", re.IGNORECASE)
        tutela = re.compile(r"Tutela|Urgência", re.IGNORECASE)

    
        if not deferimento.search(full_text) or not tutela.search(full_text):
            
            '''
            analysed_ids.append(document_id)
            maior_id = max((doc for doc in tipos_encontrados if doc[0] not in analysed_ids),key=lambda x: x[0], default=None)
            if maior_id is not None:
                tipo =  maior_id[3]
                documento = maior_id[2]
                maior_id=maior_id[0]
                analysed_ids.append(maior_id)
                extract_document_by_id(pdf_path,maior_id,tipo,documento,output_path,filename,tipos_encontrados,contagem_peticoes)
            ''' 
            try:
                id_selecionado,documento,tipo = select_id_to_analyze(tipos_encontrados,analysed_ids)
            except Exception as e:
                id_selecionado = None
            if id_selecionado:
                #extract_document_by_id(pdf_path,maior_id,tipo,documento,output_path,filename,tipos_encontrados,contagem_peticoes)
                extract_document_by_id(pdf_path,id_selecionado,tipo,documento,output_path,filename,tipos_encontrados,contagem_peticoes)
                return
            else:
                #check_document_types
                forca_peticao =1
                interesses = ["Petição Inicial", "Decisão", "Sentença",'Interlocutória']
                tipos_encontrados =  check_pdf_in_folder(folder_path, interesses,forca_peticao)
                id_pet, data_assinatura, documento, interesse = tipos_encontrados[0]
                extract_document_by_id(pdf_path,id_pet,interesse,documento,output_path,filename,tipos_encontrados,contagem_peticoes)
                return

    new_pdf.save(f"{output_path}/{filename}")
    new_pdf.close()
    pdf_document.close()
    print(f"Documento {filename} extraído e salvo em {output_path}/{filename}")

def select_id_to_analyze(tipos_encontrados, analysed_ids):

    lista_selecao = [item for item in tipos_encontrados if item not in analysed_ids]
    if not lista_selecao:
        return None  
    documento_selecionado =  lista_selecao[0]
    if len(documento_selecionado) != 4:
        return None
    id_selecionado  =documento_selecionado[0]
    documento = documento_selecionado[2]
    tipo = documento_selecionado[3]
    analysed_ids.append(documento_selecionado)
    return id_selecionado, documento, tipo


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




def CheckIdOfInterest(pdf_path,document_info,interests,forca_peticao):
   # Inicializa varávais para checar se o documento correto é realmente o selecionado
   # pelo robô
   contagem_peticoes = 0
   analysed_ids = []
   # Captura os andamentos interesse para a aplicação de portaria
   # dado a lista de andamentos do processo
   tipos_encontrados = CheckPdfInFolder(document_info, interests,forca_peticao)
   #print(tipos_encontrados)
   # Seleciona o último ID de interesse para a análise de Aplicação 
   # da portaaria  01/2017
   id_selecionado,documento,tipo =  select_id_to_analyze(tipos_encontrados,analysed_ids)
   # Faz uma série de Checagens para validar que o documento selecionado é realmente o que o Robô
   # necessita analisar
   id_revisto =  CheckPDFDocument(pdf_path,id_selecionado,tipo,documento,tipos_encontrados,contagem_peticoes,analysed_ids)
   print(id_revisto)
   return id_revisto
