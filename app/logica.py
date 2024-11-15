from flask import request, jsonify
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, DECIMAL, ForeignKey,text, schema
from sqlalchemy.orm import sessionmaker 
from AnalisePortaria import *

#Alfresco
import requests
from requests.auth import HTTPBasicAuth

import fitz  # PyMuPDF
import PyPDF2
import re
import os

import pdfplumber

# Imports despacho João Claudio

import openai
import csv
import json
import pandas as pd
import requests
from urllib.parse import urlencode
from templates import *
from article import DocumentProcessor


from datetime import datetime


DB_PARAMS = {
      'host': '192.168.2.64',
      'database': 'db_pge',
      'user': 'scm_robo',
      'password': 'x6ZP&Fc45k(<',
      'port': '5432'
  }

DATABASE_URL = f"postgresql://{DB_PARAMS['user']}:{DB_PARAMS['password']}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['database']}"

alfresco_url = "http://ccged.pge.ce.gov.br:8080"
username = "ccportalprocurador"
password = "aeH}ie0nar"
parent_node_id = "bf4f65fc-ee14-46d7-afe1-7a680f01515d"  


#Função para baixar o pdf no alfresco a partir do numero do processo
def importar_autos_alfresco(n_processo):  
      engine_alfresco = create_engine(DATABASE_URL)
      Session_alfresco = sessionmaker(bind=engine_alfresco)  
      metadata_alfresco = MetaData()
      
      session_alfresco = Session_alfresco()
      query = text('SELECT numerounico, idalfresco,id FROM scm_robo_intimacao.tb_autosprocessos WHERE numerounico = :numero_processo')
      resultado_alfresco = session_alfresco.execute(query, {"numero_processo": n_processo}).fetchone()

      id_alfresco =  resultado_alfresco[1]
      id_processo = resultado_alfresco[2]
      
      session_alfresco.commit()

      download_url = f"{alfresco_url}/alfresco/api/-default-/public/alfresco/versions/1/nodes/{id_alfresco}/content"
      try:
          response = requests.get(download_url, auth=HTTPBasicAuth(username, password))
          if response.status_code == 200:
              content_type = response.headers.get('Content-Type')
              file_extension = content_type.split(';')[0]
              if file_extension == 'application/vnd.oasis.opendocument.text':
                  file_extension = 'odt'
              elif file_extension == 'application/pdf':
                  file_extension = 'pdf'
              elif file_extension == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                  file_extension = 'docx'
              else:
                  return False
              path = f"arquivos/{id_processo}.{file_extension}"
              with open(path, 'wb') as file:  # Assumindo que o arquivo é um PDF
                  file.write(response.content)
          
      except Exception as e:
          print("Erro no donwload do arquivo: ", e)
          return False
      return path       

#Função que irá separar o documento a ser analisado pela portaria do restante dos autos 
def separar_pelo_id(path,id_andamento): 
    pdf_document = fitz.open(path)
    
    primeira_pagina = identificar_primeira_pagina(pdf_document, id_andamento)
    
    if not primeira_pagina:
        return None, None, None
    
    #pages_to_extract = []
    pages_to_extract = [0]  # Sempre inclui a primeira página, que contem valor da causa, partes, etc..
    
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text1 = page.get_text()
        if f"Num. {id_andamento} - Pág." in text1:
            pages_to_extract.append(page_num)

    new_pdf = fitz.open()

    text_length = 0 
    full_text = ""
    for page_num in pages_to_extract:
        new_pdf.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)
        page = pdf_document.load_page(page_num)
        text2 = page.get_text()
        full_text += text2
        text_length += len(text2)
        
    if not pages_to_extract:
        return None, None, None

    output_path = "temp"  
    filename = "portaria_temp.pdf"           
    file_path = f"{output_path}/{filename}"

    # Salva o novo PDF
    new_pdf.save(file_path)
    new_pdf.close()
    pdf_document.close()
    return file_path,filename, primeira_pagina



def atualizar_status(n_processo, id_andamento,session,momento): 

    if momento == 1: 
        status = 'Recebido'
        insercaoAM = session.execute(text('''
            UPDATE db_pge.scm_robo_intimacao.tb_analiseportaria
            SET status=:status
                                            
            WHERE numerounico=:n_processo;
        '''),
        {
            'status': status,
            'n_processo': n_processo
            
        })
        session.commit()
        
    elif momento == 2:
        status = 'Em Análise'
        insercaoAM = session.execute(text('''
            UPDATE db_pge.scm_robo_intimacao.tb_analiseportaria
            SET status=:status
                                            
            WHERE numerounico=:n_processo AND id_documento_analisado=:id_andamento;
        '''),
        {
            'status': status,
            'id_andamento': id_andamento,
            'n_processo': n_processo
            
        })
        session.commit()
    elif momento == 3:
        status = 'Analisado'
        insercaoAM = session.execute(text('''
            UPDATE db_pge.scm_robo_intimacao.tb_analiseportaria
            SET status=:status
                                            
            WHERE numerounico=:n_processo AND id_documento_analisado=:id_andamento;
        '''),
        {
            'status': status,
            'id_andamento': id_andamento,
            'n_processo': n_processo
            
        })
    else: 
        print('Não foi possível fazer a atualização do status') 

# Função que irá identificar a primeira página do documento a ser analisado pela portaria
def identificar_primeira_pagina(pdf_document, id_andamento):
        
    # Variável para armazenar o número da primeira página encontrada
    primeira_pagina = None

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text = page.get_text()

        # Verifica se a identificação do andamento está na página
        if f"Num. {id_andamento} - Pág." in text:
            primeira_pagina = page_num
            break  # Interrompe o loop após encontrar a primeira ocorrência
        
    #pdf_document.close()
    
    # Retorna o número da primeira página encontrada, ou None se não encontrado
    return primeira_pagina


"""
#Função para obter a primeira página de um 
def primeira_pagina(n_processo,id_andamento):
    
    path = importar_autos_alfresco(n_processo)
    file_path,filename = separar_pelo_id(path,id_andamento)
    
    if file_path is None:
        return jsonify({"error": "Não foi encontrado um documento com o id especificado!"}), 400

    pdf_document = fitz.open(file_path)
    #pages_to_extract = []
    page_num = 0
    page = pdf_document.load_page(page_num)
    new_pdf = fitz.open()
    text_length = 0 
    full_text = ""
    new_pdf.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)
    output_path = "temp"  
    filename = "primeira_pagina_temp.pdf"           
    file_path = f"{output_path}/{filename}"

    # Salva o novo PDF
    new_pdf.save(file_path)
    new_pdf.close()
    pdf_document.close()
    return file_path,filename

    # Salva o novo PDF
    new_pdf.save(file_path)
    new_pdf.close()
    pdf_document.close()
    return file_path,filename
"""


def importar_processos(SelecaoAutomaticaDocumento=False):
  
  """
  Lógica da Rota para importar os processos de intimações cujos autos já tenham sido baixados pelos
  robô de distribuição de processos (tabela tb_autosprocessos) para a tabela tb_analiseportaria
  """ 
  
  # Criar engine e sessão
  engine = create_engine(DATABASE_URL)
  Session = sessionmaker(bind=engine)
  
  # Metadados globais
  metadata = MetaData()
  # Registrar a tabela tb_autosprosaude no metadata
  tb_autosprosaude = Table(
      'tb_autosprosaude', metadata,
      Column('id', Integer, primary_key=True),
      schema='scm_robo_intimacao'
  )
      
  
  #Marcador para ignorar linha
  marca = 0

  session = Session()
  # Abre a tabela tb_autosprosaude com intimações que foram processadas
  query = text('SELECT * FROM scm_robo_intimacao.tb_autosprocessos ta WHERE ta.processado = true AND Upper(setorrequisicao) = :setor AND ta.base LIKE :base')
  resultado = session.execute(query, {"setor":"PROSAUDE","base":"%PJE%"})
  
  resultado1 = (None,None,None,None,None,None) 
  for row in resultado:    
      #Verifica se a linha já foi inserida antes
      checagem1 = session.execute(text(f'SELECT * FROM scm_robo_intimacao.tb_analiseportaria ta WHERE ta.fk_autosprosaude = {row[0]}'))
      for check in checagem1:
          if(check[1] == row[0]):
              print(f'Ignorado: Processo de no. unico {row[1]} e id {row[0]} já foi inserido')
              marca = 1
              break    
      if(marca == 1):
          marca = 0
          continue 

      #Verifica se a tabela está vazia e busca o último id inserido
      buscaultimoid = session.execute(text('SELECT * FROM scm_robo_intimacao.tb_analiseportaria ta ORDER by ta.id DESC')).first()
      if(buscaultimoid == None):
          temppk = 500

      else:
          temppk = buscaultimoid[0] + 1 

      print(f'Inserindo: Processo de no. unico {row[1]} e id {row[0]}')
    
      #fk_autosprosaude
      tempfk = row[0]
      
      #numerounico
      tempNU = row[1]
      
      #caminho
      tempCA = row[4]
      
      #base
      tempbase = row[5]
      
      #dt_processado
      tempdtproc = row[8]
      
      resultado1 =(temppk,tempfk,tempNU,tempCA,tempbase,tempdtproc)
  
      insercao = session.execute(text('INSERT into scm_robo_intimacao.tb_analiseportaria (id, fk_autosprosaude, numerounico, caminho, base, dt_processado) values(:id,:fk_autosprosaude,:numerounico,:caminho,:base,:dt_processado)'),{'id':f'{temppk}','fk_autosprosaude':f'{tempfk}','numerounico':f'{tempNU}','caminho':f'{tempCA}','base':f'{tempbase}','dt_processado':f'{tempdtproc}'})
      
      session.commit()
      
      print(f'Capturando documentos: Processo de no. unico {row[1]} e id {row[0]}')
      captura_ids_processo(row[1], id=None, SelecaoAutomaticaDocumento=SelecaoAutomaticaDocumento)
      
      print(f'Inserido: Processo de no. unico {row[1]} e id {row[0]}')
    
      atualizar_status(n_processo = tempNU,id_andamento = None,momento = 1,session= session) 
      
      ############    

  session.commit()

  return jsonify(resultado1), 200
   
def analisar_marcados():

  """
  Lógica da Rota para analisar todos os processos da tabela tb_analiseportaria tais que:
    - não tenham sido ainda analisados
    - estejam marcados para análise 
    - possuam o campo id_documento definido
  """


  # Criar engine e sessão
  engine = create_engine(DATABASE_URL)
  Session = sessionmaker(bind=engine)
  
  # Metadados globais
  metadata = MetaData()
  # Registrar a tabela tb_autosprosaude no metadata
  tb_autosprosaude = Table(
      'tb_autosprosaude', metadata,
      Column('id', Integer, primary_key=True),
      schema='scm_robo_intimacao'
  )
  
  tb_medicamentos = Table(
    'tb_medicamentos', metadata,
    Column('id', Integer, primary_key=True),
    schema='scm_robo_intimacao'
  )

  session = Session()
  # Pesquisa o processo em tb_analiseportaria
  query = text('SELECT numerounico,marcado_analisar,id_documento_analisado FROM scm_robo_intimacao.tb_analiseportaria ta WHERE ta.analisado is not true and ta.marcado_analisar is true and ta.id_documento_analisado is not null')
  resultados = session.execute(query).fetchall()
  
  for resultado in resultados:
      n_processo = resultado[0]     
      id_andamento = resultado[2]  
      atualizar_status(n_processo,id_andamento,session,momento = 2) 
      resposta = analisa(n_processo, id_andamento)
      
      if isinstance(resposta, dict):
          grava_resultado_BD(n_processo, id_andamento, resposta, session)
          gerar_despacho(n_processo,session,resposta)
          atualizar_status(n_processo,id_andamento,session,momento = 3) 
      else:
          #return jsonify(resposta), 400
          print(resposta)
  
  # Retorna a resposta com o resultado do processamento
  return jsonify({"message": "Processos analisados com sucesso."}), 200
      
  
      
def analisar_processo(numero_processo):
  """
  Lógica da Rota de análise de aplicação de portaria para um processo.
  A rota recebe um número de processo como parâmetro e executa diversas etapas necessárias para
  análise, desde a recuperação dos autos no Alfresco, até a extração do documento a ser analisado
  e aplicação do pipeline de análise de aplicação de portaria
  
  Parâmetros:
  - numero_processo (form): Número do processo a ser analisado.
  
  Fluxo:
  1. Validação do número de processo e mesmo foi marcado para análise.
  2. Download dos autos completos do processo (Alfresco).
  3. Processamento dos autos para extrair o documento a ser analisado
  4. Execução do pipeline de Análise.
  5. Escrita dos resultados da análise no BD.
  """    
  
  numero_processo = request.form.get('numero_processo')
  #TODO: Verificar casos em que o número não tenha sido passado no formato padrão
  

  # Criar engine e sessão
  engine = create_engine(DATABASE_URL)
  Session = sessionmaker(bind=engine)
  
  # Metadados globais
  metadata = MetaData()
  # Registrar a tabela tb_autosprosaude no metadata
  tb_autosprosaude = Table(
      'tb_autosprosaude', metadata,
      Column('id', Integer, primary_key=True),
      schema='scm_robo_intimacao'
  )

  session = Session()
  # Pesquisa o processo em tb_analiseportaria
  query = text('SELECT numerounico,marcado_analisar,id_documento_analisado,analisado FROM scm_robo_intimacao.tb_analiseportaria ta WHERE ta.numerounico =:numeroprocesso and ta.analisado is not true and ta.marcado_analisar is true and ta.id_documento_analisado is not null')
  #ta.analisado is not true
  resultado = session.execute(query, {"numeroprocesso":numero_processo}).fetchone()
  n_processo =  resultado[0]
  id_andamento = resultado[2]
  atualizar_status(n_processo,id_andamento,session,momento = 2) 

  resposta = analisa(n_processo, id_andamento)
  
  if isinstance(resposta, dict):
    grava_resultado_BD(n_processo, id_andamento, resposta, session)
    gerar_despacho(n_processo,session,resposta)
    atualizar_status(n_processo,id_andamento,session,momento = 3) 
  else:
    return resposta
  
  # Retorna a resposta com o resultado do processamento
  return jsonify({"message": "Processo atualizado com sucesso."}), 200


def analisa(n_processo, id_andamento):
      """
      Lógica que recebe número único do processo e id do documento e chama
      o robô de análise para gerar o dicionário com todas as informações
      """    
      #Função para baixar o pdf no alfresco a partir do numero do processo
      path = importar_autos_alfresco(n_processo)
     
      if path is False:
        return jsonify({"error":"Processo não encontrado no Alfresco!"}), 400  
      
      # Função para separar a peça dado o id do documento
      file_path,filename, primeira_pagina = separar_pelo_id(path,id_andamento)
      
      if file_path is None:
        return jsonify({"error": "Não foi encontrado um documento com o id especificado!"}), 400
      
      #pdf_file = fitz.open(file_path)

      with open(file_path, 'rb') as file:
        pdf_content = file.read()

      if len(pdf_content) == 0:
        return jsonify({"error": "O arquivo enviado está vazio!"}), 400
        

      pdf_filename = filename
      file_path = os.path.join('temp', pdf_filename)      
      
      models = {
      "honorarios" : "gpt-4o",
      "doutros" : "gpt-4o",
      "medicamentos" : "gpt-4o",
      "alimentares" : "gpt-4o",
      "internacao" : "gpt-4o",      
      "resumo" : "gpt-4o",
      "geral" : "gpt-4o"
      }

      try:
        
        resposta = AnalisePortaria(file_path, models, pdf_filename, Verbose=True) 
      
      except Exception as e:
        return jsonify({"error":f"Não foi possível analisar o processo{n_processo}"}), 400
      
      
      if not isinstance(resposta, dict):
        return jsonify({"error":"O retorno de AnalisePortaria não é um dicionário"}), 400

      
      #
      resposta['primeira_pagina'] = primeira_pagina + 1
      
      #if os.path.isfile(path):
      #    os.remove(path) 
      
      return resposta



def grava_resultado_BD(n_processo, id_andamento, resultado, session):

    # ATUALIZAÇÃO COM OS RESULTADOS DA ANÁLISE
    textosql = text(f"""
        UPDATE db_pge.scm_robo_intimacao.tb_analiseportaria ta 
        SET tipo_documento = :tipo_documento, 
        analisado = :analisado, 
        aplica_portaria = :aplica_portaria, 
        possui_medicamentos = :possui_medicamentos, 
        possui_internacao = :possui_internacao, 
        possui_consultas_exames_procedimentos = :possui_consultas_exames_procedimentos, 
        possui_insulina = :possui_insulina, 
        possui_insumos = :possui_insumos, 
        possui_multidisciplinar = :possui_multidisciplinar, 
        possui_custeio = :possui_custeio, 
        possui_compostos = :possui_compostos, 
        possui_condenacao_honorarios = :possui_condenacao_honorarios,  
        possui_danos_morais = :possui_danos_morais, 
        lista_outros = :lista_outros, 
        custo_analise = :custo_analise, 
        input_tokens = :input_tokens,
        completion_tokens = :completion_tokens,
        resumo =:resumo, 
        resumo_analise =:resumo_analise,
        marcado_analisar =:marcado_analisar, 
        dt_analisado =:dt_analisado,
        pagina_analisada =:pagina_analisada, 
        id_documento_analisado =:id_analisado 
        WHERE ta.numerounico=:numero_processo
    """)

    session.execute(textosql, {
        'tipo_documento': resultado['tipo_documento'],
        'analisado': True,
        'aplica_portaria': any(resultado['aplicacao_incisos']),
        'possui_medicamentos': len(resultado['lista_medicamentos']) > 0,
        'possui_internacao': resultado['internacao'] if resultado['internacao'] is not None else False,
        'possui_consultas_exames_procedimentos': resultado['possui_consulta'] if resultado['possui_consulta'] is not None else False,
        'possui_insulina': len(resultado['lista_glicemico']) > 0,
        'possui_insumos': len(resultado['lista_insumos']) > 0,
        'possui_multidisciplinar': len(resultado['lista_tratamento']) > 0,
        'possui_custeio': resultado['possui_custeio'] if resultado['possui_custeio'] is not None else False,
        'possui_compostos': len(resultado['lista_compostos']) > 0,
        'possui_condenacao_honorarios': resultado['condenacao_honorarios'] if resultado['condenacao_honorarios'] is not None else False,
        'possui_danos_morais': resultado['indenizacao'] if resultado['indenizacao'] is not None else False,
        'respeita_valor_teto': resultado['respeita_valor_teto'] if resultado['respeita_valor_teto'] is not None else False,
        'lista_outros': resultado['lista_outros'],
        'custo_analise': resultado['custollm'],
        'input_tokens': resultado['tokensllm'][0],
        'completion_tokens': resultado['tokensllm'][1],
        'numero_processo': n_processo,
        'resumo': resultado['resumo'],
        'resumo_analise': resultado['resumo_analise'],
        'marcado_analisar': True,
        'dt_analisado': datetime.now(),
        'pagina_analisada': resultado['primeira_pagina'] if 'primeira_pagina' in resultado else None,
        'id_analisado': id_andamento
    })

    # INSERÇÃO NA TABELA DE MEDICAMENTOS
    for medicamento in resultado['lista_medicamentos']:
        textosql1 = text("SELECT * from db_pge.scm_robo_intimacao.tb_analiseportaria ta WHERE ta.numerounico =:numero_processo")
        buscaidportaria = session.execute(textosql1, {'numero_processo': n_processo}).fetchone()
        idportaria = buscaidportaria[0]
        
        buscaultimoid = session.execute(text("SELECT MAX(tm.id) from db_pge.scm_robo_intimacao.tb_medicamentos tm")).fetchone()
        idmedicamento = (buscaultimoid[0] or 799) + 1

        insercaoAM = session.execute(text("""
            INSERT into db_pge.scm_robo_intimacao.tb_medicamentos 
            (id, id_analiseportaria, nome_principio, nome_comercial, dosagem, possui_anvisa, registro_anvisa, fornecido_SUS, valor) 
            values(:id, :id_analiseportaria, :nome_principio, :nome_comercial, :dosagem, :possui_anvisa, :registro_anvisa, :fornecido_SUS, :valor)
        """), {
            'id': idmedicamento,
            'id_analiseportaria': idportaria,
            'nome_principio': medicamento['nome_principio'],
            'nome_comercial': medicamento['nome_comercial'],
            'dosagem': medicamento['dosagem'],
            'possui_anvisa': medicamento['registro_anvisa'] is not None,
            'registro_anvisa': medicamento['registro_anvisa'],
            'fornecido_SUS': medicamento['oferta_SUS'] or False,
            'valor': medicamento['preco_PMVG'].replace('R$', '')
        })
        
    
    # INSERÇÃO NA TABELA DE COMPOSTOS ALIMENTARES
    for alimento in resultado['lista_compostos']:
        textosql1 = text("SELECT * from db_pge.scm_robo_intimacao.tb_analiseportaria ta WHERE ta.numerounico =:numero_processo")
        buscaidportaria = session.execute(textosql1, {'numero_processo': n_processo}).fetchone()
        idportaria = buscaidportaria[0]

        buscaultimoid = session.execute(text("SELECT MAX(tc.id) from db_pge.scm_robo_intimacao.tb_compostos tc")).fetchone()
        idcomposto = (buscaultimoid[0] or 0) + 1  # Incrementa o ID, começando de 1 se vazio

        insercaoAC = session.execute(text("""
            INSERT into db_pge.scm_robo_intimacao.tb_compostos
            (id, id_analiseportaria, nome_composto, qtde, duracao, possui_anvisa, registro_anvisa, valor)
            values(:id, :id_analiseportaria, :nome_composto, :qtde, :duracao, :possui_anvisa, :registro_anvisa, :valor)
        """), {
            'id': idcomposto,
            'id_analiseportaria': idportaria,
            'nome_composto': alimento['nome'],
            'qtde': alimento['quantidade'],
            'duracao': alimento['duracao'],
            'possui_anvisa': alimento.get('possui_anvisa', None),
            'registro_anvisa': alimento.get('registro_anvisa', None),
            'valor': alimento.get('valor', None)
        })
    
    
    session.commit()



# Captura os ids dos documentos e suas informações a partir de um processo (e o id, pois podem haver vários processos com o mesmo numerounico)
# Preenche essas informações no banco de dados tabela tb_documentos
def captura_ids_processo(n_processo, id=None, SelecaoAutomaticaDocumento=False):
    
    """
    path = importar_autos_alfresco(n_processo)
    #Função para capturar o id_analise portaria dado o número do processo
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)

    metadata = MetaData()
    session = Session()
    # Pesquisa o id da análise no banco pelo número do processo
    query = text('SELECT numerounico, id FROM scm_robo_intimacao.tb_analiseportaria ta WHERE ta.numerounico =:numeroprocesso')
    resultado = session.execute(query, {"numeroprocesso":n_processo}).fetchone()
    id_analiseportaria =  resultado[1]
    """
    
    path = importar_autos_alfresco(n_processo)
    # Função para capturar o id_analiseportaria dado o número do processo
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)

    metadata = MetaData()
    session = Session()

    if SelecaoAutomaticaDocumento == True:
        print('A Fazer')

    # Se um ID for passado, usa-o diretamente; caso contrário, faz a consulta
    if id is not None:
        id_analiseportaria = id
    else:
        # Pesquisa o id da análise no banco pelo número do processo
        query = text('SELECT numerounico, id FROM scm_robo_intimacao.tb_analiseportaria ta WHERE ta.numerounico =:numeroprocesso')
        resultado = session.execute(query, {"numeroprocesso": n_processo}).fetchone()
        if resultado:
            id_analiseportaria = resultado[1]
        else:
            # Se não houver resultado, encerra a função com uma indicação de falha
            session.close()
            pdf_document.close()
            if os.path.isfile(path):
                os.remove(path)
            return False

    # Captura os ids dos andamentos dentro de um processo
    pdf_document = pdfplumber.open(path)
    document_info = []

    for page_num,page in enumerate(pdf_document.pages):
        texto = page.extract_text()
        
        # Verifica se a página tem o padrão "Num. \d{8} - Pág. \d+"
        if not re.search(r"Num\. \d{8} - Pág\. \d+", texto):
            # Unir linhas quebradas
            texto = re.sub(r"\n", " ", texto)
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
                        print(f"Erro ao processar {n_processo}: {e}")
                        continue 
    for dados in document_info:
        try:
            id_doc = dados[0]
            data_assinatura = dados[1].replace('\n',' ')
            documento = dados[2].replace('\n',' ')
            tipo = dados[3]
            res =  session.execute(text('SELECT Max(id) as valor_max FROM db_pge.scm_robo_intimacao.tb_documentosautos')).fetchone()
            max_id = res[0] + 1
            query_check = text('SELECT numerounico,id_documento FROM db_pge.scm_robo_intimacao.tb_documentosautos WHERE numerounico = :numeroprocesso AND id_documento = :iddocumento')
            check = session.execute(query_check, {"numeroprocesso":n_processo,"iddocumento": id_doc}).fetchone()
            if check is None:
                insercao = session.execute(text('INSERT into db_pge.scm_robo_intimacao.tb_documentosautos (id, numerounico, id_documento, dt_assinatura, nome,  tipo, id_analiseportaria)values(:id, :numerounico, :id_documento,:dt_assinatura, :nome, :tipo, :id_analiseportaria)'),{'id':max_id,'numerounico':n_processo,'id_documento':id_doc,'dt_assinatura':data_assinatura,'nome':f'{documento}','tipo':tipo,'id_analiseportaria':id_analiseportaria})
            else: 
                continue
        except Exception as e:
            print(f"Erro ao processar {n_processo}: {e}")
            continue 


    session.commit()            
    pdf_document.close()
    if os.path.isfile(path):
        os.remove(path) 
    return True

def encontrar_arquivo(nome_arquivo):
    
    nome_arquivo_comp = f"{nome_arquivo}.pdf"
    diretorio_arquivos = f'arquivos/'  
    for raiz, _, arquivos in os.walk(diretorio_arquivos):
        if nome_arquivo_comp in arquivos:
            caminho_completo = os.path.join(raiz, nome_arquivo_comp)
            return caminho_completo
    return False

#  ler o texto do PDF
def read_pdf(file_path):
    from PyPDF2 import PdfReader

    with open(file_path, 'rb') as file:
        reader = PdfReader(file)
        text = ''
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
    return text

# dividir o texto em partes menores
def split_text(text, max_length):
    words = text.split()
    current_length = 0
    current_chunk = []
    chunks = []

    for word in words:
        current_length += len(word) + 1  # +1 para o espaço
        if current_length > max_length:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word) + 1
        else:
            current_chunk.append(word)

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks



def get_specific_info(text, api_key):

    openai.api_key = api_key
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você é um jurista especializado em decisões judiciais."},
                {"role": "user", "content": f"Extraia as seguintes informações do texto judicial:\n\n\
                1. Identificação do Despacho: Indicação de que se trata de uma sentença judicial.\n\
                2. Decisão sobre o Pleito: Indicação de que o pleito autoral foi julgado procedente e a decisão antecipatória de tutela foi ratificada.\n\
                3. Especificação do Medicamento: Nome do medicamento e detalhes, como a dosagem. Confirmação de que o medicamento está registrado na ANVISA.\n\
                4. Danos Morais: Afirmativa sobre a ausência de danos morais.\n\
                5. Direcionamentos Finais: Instruções sobre não interpor recurso se cabível. Orientações para comunicar a Secretaria de Estado da Saúde (SESA) ou outras entidades sobre a decisão. Direções sobre arquivamento do processo conforme orientação da chefia.\n\
                \nTexto: {text}"}
            ]
        )
        extracted_info = response.choices[0].message.content.strip()
        return extracted_info
    except Exception as e:
        print(f"Error during API call: {e}")
        return ""


# processar todos os PDFs de uma pasta no Google Drive
def process_pdfs_from_drive(file_path, api_key):
    extracted_data = []

    #for filename in os.listdir(folder_path):
        #if filename.endswith(".pdf"):
    #file_path = os.path.join(folder_path, filename)
    pdf_text = read_pdf(file_path)
    chunks = split_text(pdf_text, 10000)

    full_text = ""
    for chunk in chunks:
        full_text += chunk

    # Extrair informações do texto completo
    extracted_info = get_specific_info(full_text, api_key)
    filename = os.path.basename(file_path)
    extracted_data.append((filename, extracted_info))

    return extracted_data

def grava_despacho_bd(fk,despacho,session):
    insercaoAM = session.execute(text('''
            UPDATE db_pge.scm_robo_intimacao.tb_analiseportaria
            SET despacho_gerado=:despacho
                                            
            WHERE fk_autosprosaude=:fk;
        '''), {
            'despacho': despacho,
            'fk': fk
            
        })
    session.commit()

def selecionar_template(resultado_analise):
    if resultado_analise['tipo_documento'] == 'Sentença' and any(resultado_analise['aplicacao_incisos']) is True and len(resultado_analise['lista_medicamentos']) > 0:       
        data = {
        "template": TEMPLATE_sentenca_MEDICAMENTO
        }
        print('Template Sentença - Medicamento')
        
    elif resultado_analise['tipo_documento'] == 'Decisão Interlocutória' and any(resultado_analise['aplicacao_incisos']) is True and len(resultado_analise['lista_medicamentos']) > 0:
        data = {
        "template": TEMPLATE_DECISAO_MEDICAMENTO
        }
        print('Template Decisão - Medicamento')
    elif resultado_analise['tipo_documento'] == 'Sentença' and any(resultado_analise['aplicacao_incisos']) is True and resultado_analise['internacao'] is True:
        data = {
        "template": TEMPLATE_sentenca_INTERNACAO
        }
        print('Template Sentença - Internação')
        
    elif resultado_analise['tipo_documento'] == 'Decisão Interlocutória' and any(resultado_analise['aplicacao_incisos']) is True and resultado_analise['internacao'] is True:
        data = {
        "template": TEMPLATE_DECISAO_INTERNACAO
        }
        print('Template Decisão - Internação')
    elif resultado_analise['tipo_documento'] == 'Sentença' and any(resultado_analise['aplicacao_incisos']) is True and len(resultado_analise['lista_compostos']) > 0:
        data = {
        "template": TEMPLATE_SENTENCA_COMPOSTO_ALIMENTAR
        }
        print('Template Sentença - Composto Alimentar')

    elif resultado_analise['tipo_documento'] == 'Decisão Interlocutória' and any(resultado_analise['aplicacao_incisos']) is True and len(resultado_analise['lista_compostos']) > 0:
        data = {
        "template": TEMPLATE_DECISAO_COMPOSTO_ALIMENTAR
        }
        print('Template Decisão- Composto Alimentar')
    elif resultado_analise['tipo_documento'] == 'Sentença' and any(resultado_analise['aplicacao_incisos']) is True and (('cirurgia' in resultado_analise['lista_outros']) or ('procedimento' in resultado_analise['lista_outros'])):
        data = {
        "template": TEMPLATE_sentenca_CIRURGIA
        }
        print('Template Sentença - Cirurgia')

    elif resultado_analise['tipo_documento'] == 'Decisão Interlocutória' and any(resultado_analise['aplicacao_incisos']) is True and (('cirurgia' in resultado_analise['lista_outros']) or ('procedimento' in resultado_analise['lista_outros'])):
        data = {
        "template": TEMPLATE_DECISAO_cirugia
        }
        print('Template Decisão - Cirurgia')

    elif resultado_analise['tipo_documento'] == 'Sentença' and any(resultado_analise['aplicacao_incisos']) is True and ('exame' in resultado_analise['lista_outros']):
        data = {
        "template": TEMPLATE_sentenca_EXAMES
        }
        print('Template Sentença - Exame')    

    elif resultado_analise['tipo_documento'] == 'Decisão Interlocutória' and any(resultado_analise['aplicacao_incisos']) is True and ('exame' in resultado_analise['lista_outros']):
        data = {
        "template": TEMPLATE_DECISAO_exame
        }
        print('Template Decisão - Exame')  

    elif resultado_analise['tipo_documento'] == 'Sentença' and any(resultado_analise['aplicacao_incisos']) is True and (('consulta' in resultado_analise['lista_outros']) or ('atendimento' in resultado_analise['lista_outros'])):
        data = {
        "template": TEMPLATE_sentenca_CONSULTA
        }
        print('Template Sentença - Consulta')  

    elif resultado_analise['tipo_documento'] == 'Decisão Interlocutória' and any(resultado_analise['aplicacao_incisos']) is True and (('consulta' in resultado_analise['lista_outros']) or ('atendimento' in resultado_analise['lista_outros'])):
        data = {
        "template": TEMPLATE_DECISAO_consulta
        }
        print('Template Decisão - Consulta')      

    else:  

        data = False
        print('Sem Template')
        
    return data


def gerar_despacho(n_processo,session,resultado_analise):

    ### Parte responsável pela  busca no banco de dados:
    # Pesquisa o
    query = text('SELECT ta.fk_autosprosaude,ta.possui_outros,ta.possui_medicamentos,ta.possui_condenacao_honorarios,ta.aplica_portaria,ta.numerounico,ta.dt_processado FROM scm_robo_intimacao.tb_analiseportaria ta INNER JOIN (SELECT numerounico, Max(dt_processado) AS data_max FROM db_pge.scm_robo_intimacao.tb_analiseportaria tb GROUP BY numerounico) AS tabela_data_max ON tabela_data_max.numerounico =  ta.numerounico AND tabela_data_max.data_max = ta.dt_processado  WHERE ta.analisado is true AND ta.numerounico =:numeroprocesso')
    resultado = session.execute(query, {"numeroprocesso":n_processo}).fetchone()

    nome_arquivo =  resultado[0]


    json_file_path = 'dl_extracted_data.json'

    # Estrutura de dados a ser salva
    dados_json = {
        "nome_arquivo": f"{nome_arquivo}.pdf",
        "possui_outros": resultado[1],
        "possui_medicamento": resultado[2],
        "possui_condenacao_honorario": resultado[3]
    }

    # Escrever as informações extraídas em um arquivo JSON
    with open(json_file_path, mode='w', encoding='utf-8') as file:
        json.dump(dados_json, file, ensure_ascii=False, indent=4)

    print("DataFrame convertido e salvo em formato JSON com sucesso.")

    ### Parte responsável pela análise do arquivo pdf 

    caminho_arquivo =  encontrar_arquivo(nome_arquivo)
    if caminho_arquivo is False:
        return False
    api_key = "sk-proj-P2P5NFRtGPSiQpe4HY0LT3BlbkFJq4CE1TqvPigoZHOWoxMy"

    pdf_extracted_data = process_pdfs_from_drive(caminho_arquivo, api_key)

    # Caminho do arquivo JSON
    json_file_path = 'pdf_extracted_data.json'

    # Estrutura de dados a ser salva
    data_to_save = [{"File Name": data[0], "Extracted Information": data[1]} for data in pdf_extracted_data]

    # Escrever as informações extraídas em um arquivo JSON
    with open(json_file_path, mode='w', encoding='utf-8') as file:
        json.dump(data_to_save, file, ensure_ascii=False, indent=4)

    print("Informações extraídas salvas no arquivo JSON com sucesso.")

    ## Mesclando os json em um só:

    # Carregar os arquivos JSON
    with open('dl_extracted_data.json', 'r', encoding='utf-8') as file1:
        output_dl = json.load(file1)

    with open('pdf_extracted_data.json', 'r', encoding='utf-8') as file2:
        pdf_extracted_data = json.load(file2)

    # Criar um dicionário de busca para pdf_extracted_data baseado no "File Name"
    pdf_data_dict = {item['File Name']: item for item in pdf_extracted_data}
    # Mesclar os arquivos com base no nome do arquivo
    merged_data = []
    file_name = output_dl.get("nome_arquivo")
    if file_name in pdf_data_dict:
        merged_entry = {**output_dl, **pdf_data_dict[file_name]}
        merged_data.append(merged_entry)

    # Salvar o arquivo mesclado
    with open('merged_output.json', 'w', encoding='utf-8') as output_file:
        json.dump(merged_data, output_file, ensure_ascii=False, indent=4)

    print("Os arquivos foram mesclados com sucesso.")
  
    with open('merged_output.json', 'r', encoding='utf-8') as file3:
        dadosextraidos = json.load(file3)

    # Parte responsável por gerar o despacho
    base_url = 'http://127.0.0.1:5000' # Adjust this to match your server's address and port

    #Parâmetros que o usuário deve passar
    params = {
        "knowledge_area": "SENTENCA JUDICIAL",
        'area': "SENTENCA JUDICIAL - DESPACHO MEDICO",
        'subject': (
            "SENTENCA JUDICIAL - DESPACHO MEDICO",
        ),
        'topic': (
            "SENTENCA JUDICIAL - DESPACHO MEDICO"
        ),
        'context': dadosextraidos,
    }
    # Encode the query parameters
    encoded_params = urlencode(params)

    # Construct the full URL with the query parameters
    url = f'{base_url}/projeto-template?{encoded_params}'
    print(url)

    data = selecionar_template(resultado_analise)

    if data is False:
        return False

    with requests.Session() as client:
        # Make the GET request
        response = client.post(
            url,
            json=data,
            headers={"Content-Type": "application/json"}
        )

        # Check if the request was successful
        if response.ok and response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            print(response)
        else:
            print(f"Request failed with status code {response.status_code}")

    despacho  = data['result']['sections'][0]['content'][0]['paragraph']
    grava_despacho_bd(nome_arquivo,despacho,session)


"""
def grava_resultado_BD(n_processo, id_andamento, resultado, session):

    #RESUMO
    tempRESUMO = resultado['resumo']

    
    #TIPO DE DOCUMENTO
    tempTIPODOCUMENTO = resultado['tipo_documento']
    
    #APLICAÇÃO DE PORTARIA
    tempAPLICAPORTARIA =any(resultado['aplicacao_incisos'])
    #if(True in tempAPLICAPORTARIA):
    #    tempAPLICAPORTARIA = True

    #MEDICAMENTOS
    tempLISTA_MEDICAMENTOS = resultado['lista_medicamentos']

    if(len(tempLISTA_MEDICAMENTOS)>0):
        tempPOSSUI_MEDICAMENTOS = True
    else:
        tempPOSSUI_MEDICAMENTOS = False

    #INTERNAÇÃO
    tempINTERNACAO = False if resultado['internacao'] is None else resultado['internacao']


    #CONSULTAS, EXAMES, PROCEDIMENTOS
    tempCEP = resultado['lista_intervencoes']
    if(len(tempCEP)>0):
        tempPOSSUI_CEP = True
    else:
        tempPOSSUI_CEP = False

    #INSULINA
    tempINSULINA = resultado['lista_glicemico']
    if(len(tempINSULINA)>0):
        tempPOSSUI_INSULINA = True
    else:
        tempPOSSUI_INSULINA = False

    #INSUMOS
    tempINSUMOS = resultado['lista_insumos']
    if(len(tempINSUMOS)>0):
        tempPOSSUI_INSUMOS = True
    else:
        tempPOSSUI_INSUMOS = False

    #MULTIDISCIPLINAR
    tempMULTI = resultado['lista_tratamento']
    if(len(tempMULTI)>0):
        tempPOSSUI_MULTI = True
    else:
        tempPOSSUI_MULTI = False
    
    #TETO
    tempTETO = False if resultado['respeita_valor_teto'] is None else resultado['respeita_valor_teto']

    #CUSTEIO
    tempCUSTEIO = False if resultado['possui_custeio'] is None else resultado['possui_custeio']

    #COMPOSTOS
    tempCOMPOSTOS = resultado['lista_compostos']
    if(len(tempCOMPOSTOS)>0):
        tempPOSSUI_COMPOSTOS = True
    else:
        tempPOSSUI_COMPOSTOS = False

    #DANOS MORAIS
    tempDANOS_MORAIS = False if resultado['indenizacao'] is None else resultado['indenizacao']
    
    #CONDENAÇÃO POR HONORÁRIOS
    tempCOND_HONOR = False if resultado['condenacao_honorarios'] is None else resultado['condenacao_honorarios']
    
    #OUTROS
    tempPOSSUI_OUTROS = False if resultado['possui_outros'] is None else resultado['possui_outros']
    tempLISTA_OUTROS = resultado['lista_outros']
    
    #OUTROS
    tempPOSSUI_OUTROS_IMPEDITIVOS = False if resultado['possui_outros_proibidos'] is None else resultado['possui_outros_proibidos']
    
    #CUSTO ANÁLISE
    tempCUSTO = resultado['custollm']
    
    #ATUALIZAÇÃO COM OS RESULTADOS DA ANÁLISE
    textosql = text(F"UPDATE db_pge.scm_robo_intimacao.tb_analiseportaria ta SET tipo_documento = :tipo_documento, analisado = :analisado, aplica_portaria = :aplica_portaria, possui_medicamentos = :possui_medicamentos, possui_internacao = :possui_internacao, possui_consultas_exames_procedimentos = :possui_consultas_exames_procedimentos, possui_insulina = :possui_insulina, possui_insumos = :possui_insumos, possui_multidisciplinar = :possui_multidisciplinar, possui_custeio = :possui_custeio, possui_compostos = :possui_compostos, possui_condenacao_honorarios = :possui_condenacao_honorarios,  possui_danos_morais = :possui_danos_morais, lista_outros = :lista_outros, custo_analise = :custo_analise, resumo =:resumo,marcado_analisar =:marcado_analisar, dt_analisado =:dt_analisado,id_documento_analisado =:id_analisado WHERE ta.numerounico=:numero_processo")

    '''
    inserir = session.execute(textosql,{
        'tipo_documento':f'{tempTIPODOCUMENTO}',
        'analisado':True,
        'aplica_portaria':f'{tempAPLICAPORTARIA}',
        'possui_medicamentos':f'{tempPOSSUI_MEDICAMENTOS}',
        'possui_internacao':f'{tempINTERNACAO}',
        'possui_consultas_exames_procedimentos':f'{tempPOSSUI_CEP}',
        'possui_insulina':f'{tempPOSSUI_INSULINA}',
        'possui_insumos':f'{tempPOSSUI_INSUMOS}',
        'possui_multidisciplinar':f'{tempPOSSUI_MULTI}',
        'possui_custeio':f'{tempCUSTEIO}',
        'possui_compostos':f'{tempPOSSUI_COMPOSTOS}',
        'possui_outros':f'{tempPOSSUI_OUTROS}',
        'possui_outros_impeditivos':f'{tempPOSSUI_OUTROS_IMPEDITIVOS}',
        'possui_condenacao_honorarios':f'{tempCOND_HONOR}',
        'possui_danos_morais':f'{tempDANOS_MORAIS}',
        'respeita_valor_teto':{tempTETO} ,
        'lista_outros':f'{tempLISTA_OUTROS}',
        'custo_analise':f'{tempCUSTO}',
        'numero_processo':f'{n_processo}',
        'resumo':f'{tempRESUMO}',
        'marcado_analisar' : True,
        'dt_analisado':datetime.now(),
        'id_analisado' : id_andamento})
    '''
    
    inserir = session.execute(textosql,{
        'tipo_documento':f'{tempTIPODOCUMENTO}',
        'analisado':True,
        'aplica_portaria':tempAPLICAPORTARIA,
        'possui_medicamentos':tempPOSSUI_MEDICAMENTOS,
        'possui_internacao':tempINTERNACAO,
        'possui_consultas_exames_procedimentos':tempPOSSUI_CEP,
        'possui_insulina':tempPOSSUI_INSULINA,
        'possui_insumos':tempPOSSUI_INSUMOS,
        'possui_multidisciplinar':tempPOSSUI_MULTI,
        'possui_custeio':tempCUSTEIO,
        'possui_compostos':tempPOSSUI_COMPOSTOS,
        'possui_outros':tempPOSSUI_OUTROS,
        'possui_outros_impeditivos':tempPOSSUI_OUTROS_IMPEDITIVOS,
        'possui_condenacao_honorarios':tempCOND_HONOR,
        'possui_danos_morais':tempDANOS_MORAIS,
        'respeita_valor_teto':tempTETO,
        'lista_outros':f'{tempLISTA_OUTROS}',
        'custo_analise':f'{tempCUSTO}',
        'numero_processo':f'{n_processo}',
        'resumo':f'{tempRESUMO}',
        'marcado_analisar' : True,
        'dt_analisado':datetime.now(),
        'id_analisado' : id_andamento,
        'resumo_analise': resultado['resumo_analise']})
    

    #INSERÇÃO NA TABELA DE MEDICAMENTOS
    for i in range(0,len(tempLISTA_MEDICAMENTOS)):
        #id do análise portaria
        textosql1 = text(f"SELECT * from db_pge.scm_robo_intimacao.tb_analiseportaria ta WHERE ta.numerounico =:numero_processo")
        buscaidportaria = session.execute(textosql1,{'numero_processo':f'{n_processo}'})
        idportaria = buscaidportaria[0]
        #último id inserido
        buscaultimoid = session.execute("SELECT * from tb_medicamentos tm ORDER BY tm.id")
        if(buscaultimoid == None):
            idmedicamento = 800
        else:
            idmedicamento = buscaultimoid[0] + 1
        
        nome_extraido = tempLISTA_MEDICAMENTOS[i]['nome_extraido']
        nome_principio = tempLISTA_MEDICAMENTOS[i]['nome_principio']
        nome_comercial = tempLISTA_MEDICAMENTOS[i]['nome_comercial']
        dosagem = tempLISTA_MEDICAMENTOS[i]['dosagem']
        registroanvisa = tempLISTA_MEDICAMENTOS[i]['registro_anvisa']
        if(registroanvisa != None):
            possuianvisa = True
        ofertaSUS = tempLISTA_MEDICAMENTOS[i]['oferta_SUS']
        if(ofertaSUS == None):
            ofertaSUS = False
        precoPMVG = tempLISTA_MEDICAMENTOS[i]['preco_PMVG'].replace('R$','')

        insercaoAM = session.execute(text('INSERT into db_pge.scm_robo_intimacao.tb_medicamentos (id, id_analiseportaria, nome_principio, nome_comercial, dosagem, possui_anvisa, registro_anvisa, fornecido_SUS, valor) values(:id, :id_analiseportaria, :nome_principio, :nome_comercial, :dosagem, :possui_anvisa, :registro_anvisa, :fornecido_SUS, :valor)'),{'id':f'{idmedicamento}','id_analiseportaria':f'{idportaria}','nome_principio':f'{nome_principio}','nome_comercial':f'{nome_comercial}','dosagem':f'{dosagem}','possui_anvisa':f'{possuianvisa}','registro_anvisa':f'{registroanvisa}','fornecido_SUS':f'{ofertaSUS}','valor':f'{precoPMVG}'})
    session.commit()
"""

#if __name__ =="__main__":
#    captura_ids_processo('0005003-57.2013.8.06.0156', id=None, SelecaoAutomaticaDocumento=False)
    
    
