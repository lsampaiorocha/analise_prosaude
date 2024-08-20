import fitz  # PyMuPDF
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
        matches = re.findall(
            r"(\d{8})\s+(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})\s+(.+?)\s+(.+?)(?=(?:\d{8}\s+\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})|$)",
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

def check_document_types(pdf_path, interests):
    pages_to_check = extract_pages_to_check(pdf_path)
    document_info = extract_document_info_from_pages(pdf_path, pages_to_check)
    found_types = []

    for info in document_info:
        id_doc, data_assinatura, documento, tipo = info
        for interesse in interests:
            if interesse.lower() in tipo.lower() or interesse.lower() in documento.lower():
                found_types.append((id_doc, data_assinatura, documento, interesse))

    return found_types

def check_pdf_in_folder(folder_path, interests):
    tipos_encontrados = check_document_types(pdf_path, interests)

    if tipos_encontrados:
        for tipo_encontrado in tipos_encontrados:
            id_doc, data_assinatura, documento, interesse = tipo_encontrado
        else:
            print(f"Nenhum tipo de interesse encontrado no processo {pdf_path}.")
    return tipos_encontrados

def extract_document_by_id(pdf_path, document_id, output_path,filename):
    # Abrir o PDF
    pdf_document = fitz.open(pdf_path)
    
    # Lista para armazenar páginas que mencionam o ID
    pages_to_extract = []
    
    # Iterar sobre todas as páginas para encontrar o texto mencionando o ID
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text = page.get_text()
        
        # Verificar se o ID está no texto da página
        if f"Num. {document_id} - Pág." in text:
            pages_to_extract.append(page_num)
    
    if not pages_to_extract:
        print(f"Nenhuma página encontrada para o ID {document_id}.")
        pdf_document.close()
        return
    
    # Extrair as páginas especificadas e salvar em um novo PDF
    new_pdf = fitz.open()
    for page_num in pages_to_extract:
        new_pdf.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)
    
    new_pdf.save(f"{output_path}/{filename}.pdf")
    new_pdf.close()
    pdf_document.close()
    print(f"Documento {filename} extraído e salvo em {output_path}/{filename}.pdf")

# Exemplo de uso para verificar tipos de interesse em todos os PDFs na pasta
folder_path =  r"Extrai_Docs_Autos_Completos"
out_path = r"Selecionados"
interesses = ["Petição Inicial", "Interlocutória", "Sentença", "Decisão"]

for filename in os.listdir(folder_path):
    if filename.endswith(".pdf"):
        pdf_path = os.path.join(folder_path, filename)
        print(f"Verificando o arquivo: {pdf_path}")
        tipos_encontrados = check_pdf_in_folder(folder_path, interesses)
        if tipos_encontrados:
            maior_id = max(tipos_encontrados, key=lambda x: x[0])
            maior_id=maior_id[0]
            document = os.path.join(folder_path, filename)
            extract_document_by_id(document, maior_id, out_path,filename)
        else: 
            print(f"Nenhum tipo de interesse encontrado no processo {pdf_path}.")