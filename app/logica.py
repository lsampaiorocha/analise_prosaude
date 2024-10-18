from flask import request, jsonify
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, DECIMAL, ForeignKey, text, schema
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



def importar_processos():
  
  """
  Lógica da Rota para importar os processos de intimações cujos autos já tenham sido baixados pelos
  robô de distribuição de processos (tabela tb_autosprocessos) para a tabela tb_analiseportaria
  """ 
  
  DB_PARAMS = {
      'host': '192.168.2.64',
      'database': 'db_pge',
      'user': 'scm_robo',
      'password': 'x6ZP&Fc45k(<',
      'port': '5432'
  }
  
  
  DATABASE_URL = f"postgresql://{DB_PARAMS['user']}:{DB_PARAMS['password']}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['database']}"
  
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

  #Melhoria: Faça uma função para consertarem, se passarem um da maneira que não seja a padrão

  #Função para salvar o processo na tabela tb_analiseportaria
  DB_PARAMS = {
      'host': '192.168.2.64',
      'database': 'db_pge',
      'user': 'scm_robo',
      'password': 'x6ZP&Fc45k(<',
      'port': '5432'
  }

  DATABASE_URL = f"postgresql://{DB_PARAMS['user']}:{DB_PARAMS['password']}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['database']}"
  
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
  query = text('SELECT numerounico,marcado_analisar,id_documento_analisado FROM scm_robo_intimacao.tb_analiseportaria ta WHERE ta.analisado is not true and ta.marcado_analisar is true and ta.id_documento_analisado is not null')
  resultados = session.execute(query).fetchall()
  
  for resultado in resultados:

      # Função para capturar o id do alfresco através do número do processo        
      engine2 = create_engine(DATABASE_URL)
      Session2 = sessionmaker(bind=engine2)  
      metadata2 = MetaData()
      tb_autosprosaude = Table(
              'tb_autosprosaude', metadata2,
              Column('id', Integer, primary_key=True),
              schema='scm_robo_intimacao'
          )
              
      n_processo = resultado[0]     
      id_andamento = resultado[2]   

      session2 = Session()
      query = text('SELECT numerounico, idalfresco FROM scm_robo_intimacao.tb_autosprocessos WHERE numerounico = :numero_processo')
      resultado4 = session2.execute(query, {"numero_processo": n_processo}).fetchone()



      id_alfresco =  resultado4[1]
      
      session2.commit()

      #Função para baixar o pdf a partir do id do alfresco

      alfresco_url = "http://ccged.pge.ce.gov.br:8080"
      username = "ccportalprocurador"
      password = "aeH}ie0nar"
      parent_node_id = "bf4f65fc-ee14-46d7-afe1-7a680f01515d"


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
                  print("Retorna True")
                  return True
              path = f"arquivos/{id_alfresco}.{file_extension}"
              with open(path, 'wb') as file:  # Assumindo que o arquivo é um PDF
                  file.write(response.content)
          
      except Exception as e:
          print("Erro no donwload do arquivo: ", e)
          return False
      
      # Função para separar a peça dado o id do documento
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

      output_path = "temp"  
      filename = "portaria_temp.pdf"           
      file_path = f"{output_path}/{filename}"

      # Salva o novo PDF
      new_pdf.save(file_path)
      new_pdf.close()
      pdf_document.close()

      pdf_file = fitz.open(file_path)

      with open(file_path, 'rb') as file:
          pdf_content = file.read()

      if len(pdf_content) == 0:
          return jsonify({"error": "O arquivo enviado está vazio!"}), 400
      
      #pdf_filename = f"{id_andamento}_{filename}"
      pdf_filename = filename
      file_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
      #pdf_file.save(file_path)

      
      
      models = {
      "honorarios" : "gpt-4o",
      "doutros" : "gpt-4o",
      "medicamentos" : "gpt-4o",
      "alimentares" : "gpt-4o",
      "internacao" : "gpt-4o",      
      "resumo" : "gpt-4o",
      "geral" : "gpt-4o"
      }
      
      
      # Aqui você pode processar o arquivo e o ID como quiser
      resultado2 = AnalisePortaria(file_path, models, pdf_filename, Verbose=False) 
      
      if os.path.isfile(path):
          os.remove(path) 

      engine3 = create_engine(DATABASE_URL)
      Session3 = sessionmaker(bind=engine3)

      # Metadados globais
      metadata = MetaData()

      session3 = Session()

      #RESUMO
      tempRESUMO = resultado2['resumo']

      
      #TIPO DE DOCUMENTO
      tempTIPODOCUMENTO = resultado2['tipo_documento']
      
      #APLICAÇÃO DE PORTARIA
      tempAPLICAPORTARIA =any(resultado2['aplicacao_incisos'])
      #if(True in tempAPLICAPORTARIA):
      #    tempAPLICAPORTARIA = True

      #MEDICAMENTOS
      tempLISTA_MEDICAMENTOS = resultado2['lista_medicamentos']

      if(len(tempLISTA_MEDICAMENTOS)>0):
          tempPOSSUI_MEDICAMENTOS = True
      else:
          tempPOSSUI_MEDICAMENTOS = False

      #INTERNAÇÃO
      tempINTERNACAO = False if resultado2['internacao'] is None else resultado2['internacao']
  

      #CONSULTAS, EXAMES, PROCEDIMENTOS
      tempCEP = resultado2['lista_intervencoes']
      if(len(tempCEP)>0):
          tempPOSSUI_CEP = True
      else:
          tempPOSSUI_CEP = False

      #INSULINA
      tempINSULINA = resultado2['lista_glicemico']
      if(len(tempINSULINA)>0):
          tempPOSSUI_INSULINA = True
      else:
          tempPOSSUI_INSULINA = False

      #INSUMOS
      tempINSUMOS = resultado2['lista_insumos']
      if(len(tempINSUMOS)>0):
          tempPOSSUI_INSUMOS = True
      else:
          tempPOSSUI_INSUMOS = False

      #MULTIDISCIPLINAR
      tempMULTI = resultado2['lista_tratamento']
      if(len(tempMULTI)>0):
          tempPOSSUI_MULTI = True
      else:
          tempPOSSUI_MULTI = False
      
      #CUSTEIO
      tempCUSTEIO = False if resultado2['respeita_valor_teto'] is None else resultado2['respeita_valor_teto']
      #COMPOSTOS
      tempCOMPOSTOS = resultado2['lista_compostos']
      if(len(tempCOMPOSTOS)>0):
          tempPOSSUI_COMPOSTOS = True
      else:
          tempPOSSUI_COMPOSTOS = False

      #DANOS MORAIS
      tempDANOS_MORAIS = False if resultado2['indenizacao'] is None else resultado2['indenizacao']
      
      #CONDENAÇÃO POR HONORÁRIOS
      tempCOND_HONOR = False if resultado2['condenacao_honorarios'] is None else resultado2['condenacao_honorarios']
      
      #OUTROS
      tempPOSSUI_OUTROS = False if resultado2['possui_outros'] is None else resultado2['possui_outros']
      tempLISTA_OUTROS = resultado2['lista_outros']
      
      #CUSTO ANÁLISE
      tempCUSTO = resultado2['custollm']
      
      #ATUALIZAÇÃO COM OS RESULTADOS DA ANÁLISE
      textosql = text(F"UPDATE db_pge.scm_robo_intimacao.tb_analiseportaria ta SET tipo_documento = :tipo_documento, analisado = :analisado, aplica_portaria = :aplica_portaria, possui_medicamentos = :possui_medicamentos, possui_internacao = :possui_internacao, possui_consultas_exames_procedimentos = :possui_consultas_exames_procedimentos, possui_insulina = :possui_insulina, possui_insumos = :possui_insumos, possui_multidisciplinar = :possui_multidisciplinar, possui_custeio = :possui_custeio, possui_compostos = :possui_compostos, possui_condenacao_honorarios = :possui_condenacao_honorarios,  possui_danos_morais = :possui_danos_morais, lista_outros = :lista_outros, custo_analise = :custo_analise, resumo =:resumo,marcado_analisar =:marcado_analisar, dt_analisado =:dt_analisado,id_documento_analisado =:id_analisado WHERE ta.numerounico=:numero_processo")

      inserir = session3.execute(textosql,{'tipo_documento':f'{tempTIPODOCUMENTO}','analisado':True,'aplica_portaria':f'{tempAPLICAPORTARIA}','possui_medicamentos':f'{tempPOSSUI_MEDICAMENTOS}','possui_internacao':f'{tempINTERNACAO}','possui_consultas_exames_procedimentos':f'{tempPOSSUI_CEP}','possui_insulina':f'{tempPOSSUI_INSULINA}','possui_insumos':f'{tempPOSSUI_INSUMOS}','possui_multidisciplinar':f'{tempPOSSUI_MULTI}','possui_custeio':f'{tempCUSTEIO}','possui_compostos':f'{tempPOSSUI_COMPOSTOS}','possui_condenacao_honorarios':f'{tempCOND_HONOR}','possui_danos_morais':f'{tempDANOS_MORAIS}','lista_outros':f'{tempLISTA_OUTROS}','custo_analise':f'{tempCUSTO}','numero_processo':f'{n_processo}','resumo':f'{tempRESUMO}','marcado_analisar' : True,'dt_analisado':datetime.now(),'id_analisado' : id_andamento})

      #INSERÇÃO NA TABELA DE MEDICAMENTOS
      for i in range(0,len(tempLISTA_MEDICAMENTOS)):
          #id do análise portaria
          textosql1 = text(f"SELECT * from db_pge.scm_robo_intimacao.tb_analiseportaria ta WHERE ta.numerounico =:numero_processo")
          buscaidportaria = session3.execute(textosql1,{'numero_processo':f'{n_processo}'})
          idportaria = buscaidportaria[0]
          #último id inserido
          buscaultimoid = session3.execute("SELECT * from tb_medicamentos tm ORDER BY tm.id")
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

          insercaoAM = session3.execute(text('INSERT into db_pge.scm_robo_intimacao.tb_medicamentos (id, id_analiseportaria, nome_principio, nome_comercial, dosagem, possui_anvisa, registro_anvisa, fornecido_SUS, valor) values(:id, :id_analiseportaria, :nome_principio, :nome_comercial, :dosagem, :possui_anvisa, :registro_anvisa, :fornecido_SUS, :valor)'),{'id':f'{idmedicamento}','id_analiseportaria':f'{idportaria}','nome_principio':f'{nome_principio}','nome_comercial':f'{nome_comercial}','dosagem':f'{dosagem}','possui_anvisa':f'{possuianvisa}','registro_anvisa':f'{registroanvisa}','fornecido_SUS':f'{ofertaSUS}','valor':f'{precoPMVG}'})
      session3.commit()

      
  # Retorna a resposta com o resultado do processamento
  return jsonify({"message": "Processo atualizado com sucesso."}), 200
      
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
  
  DB_PARAMS = {
      'host': '192.168.2.64',
      'database': 'db_pge',
      'user': 'scm_robo',
      'password': 'x6ZP&Fc45k(<',
      'port': '5432'
  }

  DATABASE_URL = f"postgresql://{DB_PARAMS['user']}:{DB_PARAMS['password']}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['database']}"
  
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
  query = text('SELECT numerounico,marcado_analisar,id_documento_analisado FROM scm_robo_intimacao.tb_analiseportaria ta WHERE ta.numerounico =:numeroprocesso')
  resultado = session.execute(query, {"numeroprocesso":numero_processo}).fetchone()
  print(resultado)
  n_processo =  resultado[0]
  marcado_analisar = resultado[1]
  id_andamento = resultado[2]
  if not n_processo:
      return jsonify({"error":"Processo não encontrado na Tabela!"}), 400
  if marcado_analisar is not True:
      return jsonify({"error":"Processo não foi marcado para analisar!"}), 400
  if not id_andamento:
      return jsonify({"error":"Não foi passado o id do Andamento!"}), 400

  # Função para capturar o id do alfresco através do número do processo        
  engine = create_engine(DATABASE_URL)
  Session = sessionmaker(bind=engine)  
  metadata = MetaData()
  tb_autosprosaude = Table(
          'tb_autosprosaude', metadata,
          Column('id', Integer, primary_key=True),
          schema='scm_robo_intimacao'
      )
          

  session = Session()
  query = text('SELECT numerounico, idalfresco FROM scm_robo_intimacao.tb_autosprocessos WHERE numerounico = :numero_processo')
  resultado = session.execute(query, {"numero_processo": n_processo}).fetchone()

  id_alfresco =  resultado[1]
  session.commit()

  #Função para baixar o pdf a partir do id do alfresco

  alfresco_url = "http://ccged.pge.ce.gov.br:8080"
  username = "ccportalprocurador"
  password = "aeH}ie0nar"
  parent_node_id = "bf4f65fc-ee14-46d7-afe1-7a680f01515d"


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
              print("Retorna True")
              return True
          path = f"arquivos/{id_alfresco}.{file_extension}"
          with open(path, 'wb') as file:  # Assumindo que o arquivo é um PDF
              file.write(response.content)
      
  except Exception as e:
      print("Erro no donwload do arquivo: ", e)
      return False
  
  # Função para separar a peça dado o id do documento
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

  output_path = "temp"  
  filename = "portaria_temp.pdf"           
  file_path = f"{output_path}/{filename}"

  # Salva o novo PDF
  new_pdf.save(file_path)
  new_pdf.close()
  pdf_document.close()

  pdf_file = fitz.open(file_path)

  with open(file_path, 'rb') as file:
      pdf_content = file.read()

  if len(pdf_content) == 0:
      return jsonify({"error": "O arquivo enviado está vazio!"}), 400
  
  #pdf_filename = f"{id_andamento}_{filename}"
  pdf_filename = filename
  file_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
  #pdf_file.save(file_path)

  
  
  models = {
    "honorarios" : "gpt-4o",
    "doutros" : "gpt-4o",
    "medicamentos" : "gpt-4o",
    "alimentares" : "gpt-4o",
    "internacao" : "gpt-4o",      
    "resumo" : "gpt-4o",
    "geral" : "gpt-4o"
  }
  

  resultado = AnalisePortaria(file_path, models, pdf_filename, Verbose=False) 
  
  #if os.path.isfile(path):
  #    os.remove(path) 
  
  if os.path.isfile(file_path):
      os.remove(file_path) 


  engine = create_engine(DATABASE_URL)
  Session = sessionmaker(bind=engine)

  # Metadados globais
  metadata = MetaData()

  session = Session()

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
  
  #CUSTEIO
  tempCUSTEIO = False if resultado['respeita_valor_teto'] is None else resultado['respeita_valor_teto']
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
  
  #CUSTO ANÁLISE
  tempCUSTO = resultado['custollm']
  
  #ATUALIZAÇÃO COM OS RESULTADOS DA ANÁLISE
  textosql = text(F"UPDATE db_pge.scm_robo_intimacao.tb_analiseportaria ta SET tipo_documento = :tipo_documento, analisado = :analisado, aplica_portaria = :aplica_portaria, possui_medicamentos = :possui_medicamentos, possui_internacao = :possui_internacao, possui_consultas_exames_procedimentos = :possui_consultas_exames_procedimentos, possui_insulina = :possui_insulina, possui_insumos = :possui_insumos, possui_multidisciplinar = :possui_multidisciplinar, possui_custeio = :possui_custeio, possui_compostos = :possui_compostos, possui_condenacao_honorarios = :possui_condenacao_honorarios,  possui_danos_morais = :possui_danos_morais, lista_outros = :lista_outros, custo_analise = :custo_analise, resumo =:resumo,marcado_analisar =:marcado_analisar, dt_analisado =:dt_analisado,id_documento_analisado =:id_analisado WHERE ta.numerounico=:numero_processo")

  inserir = session.execute(textosql,{'tipo_documento':f'{tempTIPODOCUMENTO}','analisado':True,'aplica_portaria':f'{tempAPLICAPORTARIA}','possui_medicamentos':f'{tempPOSSUI_MEDICAMENTOS}','possui_internacao':f'{tempINTERNACAO}','possui_consultas_exames_procedimentos':f'{tempPOSSUI_CEP}','possui_insulina':f'{tempPOSSUI_INSULINA}','possui_insumos':f'{tempPOSSUI_INSUMOS}','possui_multidisciplinar':f'{tempPOSSUI_MULTI}','possui_custeio':f'{tempCUSTEIO}','possui_compostos':f'{tempPOSSUI_COMPOSTOS}','possui_condenacao_honorarios':f'{tempCOND_HONOR}','possui_danos_morais':f'{tempDANOS_MORAIS}','lista_outros':f'{tempLISTA_OUTROS}','custo_analise':f'{tempCUSTO}','numero_processo':f'{numero_processo}','resumo':f'{tempRESUMO}','marcado_analisar' : True,'dt_analisado':datetime.now(),'id_analisado' : id_andamento})

  #INSERÇÃO NA TABELA DE MEDICAMENTOS
  for i in range(0,len(tempLISTA_MEDICAMENTOS)):
      #id do análise portaria
      textosql1 = text(f"SELECT * from db_pge.scm_robo_intimacao.tb_analiseportaria ta WHERE ta.numerounico =:numero_processo")
      buscaidportaria = session.execute(textosql1,{'numero_processo':f'{numero_processo}'})
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

  
  # Retorna a resposta com o resultado do processamento
  return jsonify({"message": "Processo atualizado com sucesso."}), 200