import fitz  # PyMuPDF
import re

output_path = r"C:\Users\wilgner\Desktop\ELASTICSEARCH\PROSAUDE"

def extract_sentences_info(pdf_path):
    # Abrir o documento PDF
    pdf_document = fitz.open(pdf_path)
    
    # Lista para armazenar informações de sentenças
    sentences_info = []
    
    # Iterar sobre todas as páginas do PDF
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text = page.get_text()
        
        # Encontrar todas as ocorrências de sentenças com IDs de documentos, datas e documentos
        matches = re.findall(r"(\d{8})\s+(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})\s+(.*?)\s+Petição", text, re.IGNORECASE)
        
        for match in matches:
            id_doc = match[0]
            data_assinatura = match[1]
            documento = match[2]
            
            # Armazenar informações de sentença encontradas
            sentences_info.append((id_doc, data_assinatura, documento, "Petição"))
    
    pdf_document.close()
    
    return sentences_info

def extract_document_by_id(pdf_path, document_id, output_path):
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
    
    new_pdf.save(f"{output_path}/{document_id}.pdf")
    new_pdf.close()
    pdf_document.close()
    print(f"Documento {document_id} extraído e salvo em {output_path}/{document_id}.pdf")

# Exemplo de uso
pdf_path = r"C:\Users\wilgner\Desktop\ELASTICSEARCH/PROSAUDE/PjeautosAPI/Pjeautos/processosbaixados/AUTOS/II/0005227-69.2019.8.06.0031-1715042010674-1859581-processo.pdf"
sentences_info = extract_sentences_info(pdf_path)

# Imprimir resultados e extrair documentos
for info in sentences_info:
    id_doc, data_assinatura, documento, tipo = info
    print(f"Id: {id_doc}")
    print(f"Data da Assinatura: {data_assinatura}")
    print(f"Documento: {documento}")
    print(f"Tipo: {tipo}")
    print("-" * 50)
    # Extrair e salvar o documento correspondente ao ID
    extract_document_by_id(pdf_path, id_doc, output_path)
