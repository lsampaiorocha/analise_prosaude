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
      query = text('SELECT numerounico, idalfresco FROM scm_robo_intimacao.tb_autosprocessos WHERE numerounico = :numero_processo')
      resultado_alfresco = session_alfresco.execute(query, {"numero_processo": n_processo}).fetchone()

      id_alfresco =  resultado_alfresco[1]
      
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
              path = f"arquivos/{id_alfresco}.{file_extension}"
              with open(path, 'wb') as file:  # Assumindo que o arquivo é um PDF
                  file.write(response.content)
          
      except Exception as e:
          print("Erro no donwload do arquivo: ", e)
          return False
      return path       

#Função que irá separar o documento a ser analisado pela portaria do restante dos autos 
def separar_pelo_id(path,id_andamento): 
    pdf_document = fitz.open(path)
    pages_to_extract = []
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
        return None, None

    output_path = "temp"  
    filename = "portaria_temp.pdf"           
    file_path = f"{output_path}/{filename}"

    # Salva o novo PDF
    new_pdf.save(file_path)
    new_pdf.close()
    pdf_document.close()
    return file_path,filename

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

def importar_processos():
  
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
              print('Elemento já inserido')
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
      resposta = analisa(n_processo, id_andamento)
      
      if isinstance(resposta, dict):
          grava_resultado_BD(n_processo, id_andamento, resposta, session)
      else:
          return jsonify(resposta), 400
  
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

  resposta = analisa(n_processo, id_andamento)
  
  if isinstance(resposta, dict):
    grava_resultado_BD(n_processo, id_andamento, resposta, session)
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
      file_path,filename = separar_pelo_id(path,id_andamento)
      
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

      resposta = AnalisePortaria(file_path, models, pdf_filename, Verbose=True) 
      
      if os.path.isfile(path):
          os.remove(path) 
      
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
    session.commit()








def captura_ids_processo(n_processo):

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

    # Captura os ids dos andamentos dentro de um processo
    pdf_document = fitz.open(path)

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        texto = page.get_text("text")
        
        # Verifica se a página tem o padrão "Num. \d{8} - Pág. \d+"
        if not re.search(r"Num\. \d{8} - Pág\. \d+", texto):
            # Unir linhas quebradas
            texto = re.sub(r"\n", " ", texto)

            # Regex para encontrar linhas que correspondem à estrutura da tabela de índices
            matches = re.findall(
                r"(\d+)\s+(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})\s+(.+?)\s+(.+?)(?=(?:\d+\s+\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})|$)",
                texto
            )
            for match in matches:
                id_doc = match[0]
                data_assinatura = match[1]
                documento = match[2]
                tipo = match[3]
                res =  session.execute(text('SELECT Max(id) as valor_max FROM db_pge.scm_robo_intimacao.tb_documentosautos')).fetchone()
                max_id = res[0] + 1
                query_check = text('SELECT numerounico,id_documento FROM db_pge.scm_robo_intimacao.tb_documentosautos WHERE numerounico = :numeroprocesso AND id_documento = :iddocumento')
                check = session.execute(query_check, {"numeroprocesso":n_processo,"iddocumento": id_doc}).fetchone()
                if check is None:
                    insercao = session.execute(text('INSERT into db_pge.scm_robo_intimacao.tb_documentosautos (id, numerounico, id_documento, dt_assinatura, nome,  tipo, id_analiseportaria)values(:id, :numerounico, :id_documento,:dt_assinatura, :nome, :tipo, :id_analiseportaria)'),{'id':max_id,'numerounico':n_processo,'id_documento':id_doc,'dt_assinatura':data_assinatura,'nome':f'{documento}','tipo':tipo,'id_analiseportaria':id_analiseportaria})
                else: 
                    continue
    session.commit()            
    pdf_document.close()
    if os.path.isfile(path):
        os.remove(path) 
    return True



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
