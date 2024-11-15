import fitz  # PyMuPDF
import PyPDF2
import re
import os

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
    pdf_document = fitz.open(pdf_path)
    document_info = []

    for page_num in pages_to_check:
        page = pdf_document.load_page(page_num)
        text = page.get_text("text")

        # Unir linhas quebradas
        text = re.sub(r"\n", " ", text)
        
        # Regex para encontrar linhas que correspondem à estrutura fornecida
        '''
        matches = re.findall(
            r"(\d{8})\s+(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})\s+(.+?)\s+(.+?)(?=(?:\d{8}\s+\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})|$)",
            text
        )
        '''
        # Modificado Nathanael 09/2024
        matches = re.findall(
            r"(\d+)\s+(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})\s+(.+?)\s+(.+?)(?=(?:\d+\s+\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})|$)",
            text
            )
        for match in matches:
            id_doc = match[0]
            data_assinatura = match[1]
            documento = match[2]
            tipo = match[3]
            
            # Armazenar informações do documento encontradas
            document_info.append((id_doc, data_assinatura, documento, tipo))

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
        
        return found_types
    else:
        print('Forçou Petição')
        menor_peticao_id = min(peticao_docs, key=lambda x: x[0])[0]
        menor_peticao_docs = [doc for doc in peticao_docs if doc[0] == menor_peticao_id]
        return menor_peticao_docs

    
        
        #menor_id = min(int(info[0]) for info in document_info)
        #found_types.append((menor_id,"2024-01-01",'Petição Inicial','Petição Inicial - Forçado'))
        #return found_types

def check_pdf_in_folder(folder_path, interests,forca_peticao):
    tipos_encontrados = check_document_types(pdf_path, interests,forca_peticao)

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
                        analyzed_ids.append(document_id)
                        return document_id

    return None

#Modificado Nathanael 09/2024
def extract_document_by_id(pdf_path, document_id,tipo,documento, output_path, filename,tipos_encontrados):
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
   #print('Tamanho:',text_length)
    if text_length < 3000 and ("petição" in tipo.lower() or "petição" in documento.lower()):
        print('Menor que 3000')
        document_id = search_by_expression(pdf_path)
        extract_document_by_id(pdf_path, document_id,tipo,documento, output_path, filename,tipos_encontrados)
        return
    
    #Caso da decisão:Passa por aqui , vai checar se possui as palavras escohidas, caso não possua, atualiza
    # a lista de ids , passa novamente para capturar o novo id a ser analizado e volta pro extract documento
    
    if ("decisão" in tipo.lower() or "decisão" in documento.lower() or "decisões" in documento.lower() or "decisões" in tipo.lower()):
       
               
        deferimento = re.compile(r"Defiro|Indefiro|Deferimento|Concedo|Deferir|Acolho", re.IGNORECASE)
        tutela = re.compile(r"Tutela|Urgência", re.IGNORECASE)

    
        if not deferimento.search(full_text) or not tutela.search(full_text):
            analyzed_ids.append(document_id)
            maior_id = max((doc for doc in tipos_encontrados if doc[0] not in analyzed_ids),key=lambda x: x[0], default=None)
            if maior_id is not None:
                tipo =  maior_id[3]
                documento = maior_id[2]
                maior_id=maior_id[0]
                analyzed_ids.append(maior_id)
                extract_document_by_id(pdf_path,maior_id,tipo,documento,output_path,filename,tipos_encontrados)
                return
            else:
                #check_document_types
                forca_peticao =1
                interesses = ["Petição Inicial", "Decisão", "Sentença",'Interlocutória']
                tipos_encontrados =  check_pdf_in_folder(folder_path, interesses,forca_peticao)
                id_pet, data_assinatura, documento, interesse = tipos_encontrados[0]
                extract_document_by_id(pdf_path,id_pet,interesse,documento,output_path,filename,tipos_encontrados)
                return

    new_pdf.save(f"{output_path}/{filename}")
    new_pdf.close()
    pdf_document.close()
    return document_id
    #print(f"Documento {filename} extraído e salvo em {output_path}/{filename}.pdf")
# Exemplo de uso para verificar tipos de interesse em todos os PDFs na pasta

def Captura_id_interesse(n_processo,session):
    folder_path =  r"arquivos"
    out_path = r"temp"
    interesses = ["Petição Inicial", "Decisão", "Sentença",'Interlocutória']


    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            analyzed_ids = []
            pdf_path = os.path.join(folder_path, filename)
            print(f"Verificando o arquivo: {pdf_path}")
            forca_peticao=0
            tipos_encontrados = check_pdf_in_folder(folder_path, interesses,forca_peticao)
            if tipos_encontrados:
                maior_id = max(tipos_encontrados, key=lambda x: x[0])
                tipo =  maior_id[3]
                documento = maior_id[2]
                maior_id=maior_id[0]
                analyzed_ids.append(maior_id)
                document = os.path.join(folder_path, filename)
                extract_document_by_id(document, maior_id,tipo,documento,out_path,filename,tipos_encontrados)
            else: 
                print(f"Nenhum tipo de interesse encontrado no processo {pdf_path}.")