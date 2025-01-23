from flask import request, jsonify
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, DECIMAL, ForeignKey,text, schema
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text
 
from AnalisePortaria import *

#Alfresco
import requests
from requests.auth import HTTPBasicAuth

import fitz  # PyMuPDF
import PyPDF2
import re
import os

from datetime import datetime, timedelta

import pdfplumber

# Imports despacho João Claudio

import json
import pandas as pd
import requests
from urllib.parse import urlencode
from templates import *
from dotenv import load_dotenv


#Imports nova versao despacho

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import OpenAI
from langchain.schema.runnable import RunnableSequence


#Callback para calcular os custos da OPENAI
from langchain_community.callbacks import get_openai_callback


from datetime import datetime

from AnaliseAutos import *

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



def importar_processos():
  
    """
    Lógica da Rota para importar os processos de intimações cujos autos já tenham sido baixados pelos
    robô de distribuição de processos (tabela tb_autosprocessos) para a tabela tb_analiseportaria
    """ 

    try:
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

    except SQLAlchemyError as e:
        print(f"Erro ao conectar ao banco de dados: {str(e)}")
        return jsonify({"error": "Erro ao conectar ao banco de dados", "details": str(e)}), 500


    #Marcador para ignorar linha
    marca = 0


    # Obter a data limite para os últimos 15 dias
    data_limite = datetime.now() - timedelta(days=90)
    data_limite_str = data_limite.strftime('%Y-%m-%d')  # Formato YYYY-MM-DD

    
    # Consulta inicial para buscar os processos
    query = text('''
        SELECT id, numerounico, caminho, base, dt_processado, setorrequisicao
        FROM scm_robo_intimacao.tb_autosprocessos ta 
        WHERE ta.processado = true 
            AND Upper(ta.setorrequisicao) = :setor 
            AND ta.base LIKE :base 
            AND ta.avisonoportal = true
            AND ta.dt_processado >= :data_limite
    ''')
    
    resultados = session.execute(query, {"setor": "PROSAUDE", "base": "%PJE%", "data_limite": data_limite_str}).mappings().fetchall()

    if not resultados:
        print("Nenhum processo encontrado.")
        return jsonify({"message": "Nenhum processo encontrado."}), 200

    for row in resultados:
        # Verificar se o processo já foi inserido na tabela tb_analiseportaria
        checagem_query = text('''
            SELECT fk_autosprosaude 
            FROM scm_robo_intimacao.tb_analiseportaria ta 
            WHERE ta.fk_autosprosaude = :fk_autosprosaude
        ''')
        checagem = session.execute(checagem_query, {"fk_autosprosaude": row["id"]}).fetchone()
        
        if checagem:
            print(f"Ignorado: Processo de número único {row['numerounico']} e id {row['id']} já foi inserido.")
            continue

        # Buscar o último ID inserido na tabela tb_analiseportaria
        ultimo_id_query = text('''
            SELECT id 
            FROM scm_robo_intimacao.tb_analiseportaria 
            ORDER BY id DESC LIMIT 1
        ''')
        ultimo_id = session.execute(ultimo_id_query).scalar()
        novo_id = (ultimo_id + 1) if ultimo_id else 500

        # Preparar os dados para inserção
        dados_insercao = {
            "id": novo_id,
            "fk_autosprosaude": row["id"],
            "numerounico": row["numerounico"],
            "caminho": row["caminho"],
            "base": row["base"],
            "dt_processado": row["dt_processado"]
        }

        # Inserir o novo processo na tabela tb_analiseportaria
        insercao_query = text('''
            INSERT INTO scm_robo_intimacao.tb_analiseportaria 
            (id, fk_autosprosaude, numerounico, caminho, base, dt_processado) 
            VALUES (:id, :fk_autosprosaude, :numerounico, :caminho, :base, :dt_processado)
        ''')
        session.execute(insercao_query, dados_insercao)
        session.commit()

        print(f"Analisando Documentos dos Autos: Processo de número único {row['numerounico']} e id {row['id']}.")

        # Capturar documentos relacionados ao processo
        c = captura_ids_processo(novo_id, row["id"], id_dado=None, SelecaoAutomaticaDocumento=True)
        
        if not c:
            mensagem = f"Erro ao Analisar Documentos dos Autos: Processo de número único {row['numerounico']} e id {row['id']}."
            # Atualizar o status do processo
            atualizar_status(dados_insercao['id'], session=session, status=4)
            print(mensagem)
            continue
        

        mensagem = f"Recebido: Processo de número único {row['numerounico']} e id {row['id']}."
        print(mensagem)
        gravar_log(session, row['numerounico'], mensagem)

        # Atualizar o status do processo
        atualizar_status(dados_insercao['id'], session=session, status=1)

    # Confirmar transações pendentes
    session.commit()

    print("Processamento concluído.")
    return jsonify({"message": "Processos analisados com sucesso."}), 200
   
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
    #query = text('SELECT numerounico,marcado_analisar,id_documento_analisado FROM scm_robo_intimacao.tb_analiseportaria ta WHERE ta.analisado is not true and ta.marcado_analisar is true and ta.id_documento_analisado is not null')


    # Definir a consulta SQL para selecionar os registros desejados
    query = text('''
    SELECT
        id,
        fk_autosprosaude, 
        numerounico, 
        marcado_analisar, 
        id_documento_analisado 
    FROM scm_robo_intimacao.tb_analiseportaria ta
    WHERE ta.analisado IS NOT TRUE 
    AND ta.marcado_analisar IS TRUE
    ''')

    # Executar a consulta e buscar todos os resultados
    #resultados = session.execute(query).fetchall()
    resultados = session.execute(query).mappings().fetchall()
  
    # Iterar pelos resultados
    for resultado in resultados:
        n_processo = resultado["numerounico"]  # Usando o nome da coluna como chave
        print(n_processo)
        
        id_andamento = resultado["id_documento_analisado"]  # Usando o nome da coluna como chave
        atualizar_status(resultado["id"], session, status=2)
        mensagem = f"Iniciando Análise do processo: Número único {resultado['numerounico']} e id {resultado['id']}"
        gravar_log(session, resultado["numerounico"], mensagem)
        
        # Depois retirar o id do andamento
        resposta = analisa(resultado["fk_autosprosaude"], id_andamento, session, n_processo)
        print(id_andamento)

        # Verificar se a resposta é um dicionário
        if isinstance(resposta, dict):
            # Verificar se o dicionário contém a chave "error", em caso de algum erro
            if "error" in resposta:
                atualizar_status(resultado["id"], session, status=5)
                mensagem = f"Erro na Análise do Processo: Número único {n_processo} e id {resultado['id']} - {resposta['error']}"
                print(mensagem)
                gravar_log(session, n_processo, mensagem)
            else: #sucesso
                grava_resultado_BD(resultado["id"], id_andamento, resposta, session)
                gerar_despacho(resultado["id"], session, resposta)
                atualizar_status(resultado["id"], session, status=3)
                mensagem = f"Sucesso na Análise do Processo: Número único {n_processo} e id {resultado['id']}"
                print(mensagem)
                gravar_log(session, n_processo, mensagem)
        else:
            # Caso a resposta não seja um dicionário, trate como erro inesperado
            atualizar_status(resultado["id"], session, status=5)
            erro = resposta.get_json() if hasattr(resposta, "get_json") else str(resposta)
            mensagem = f"Erro inesperado na Análise do Processo: Número único {n_processo} e id {resultado['id']} - {erro}"
            print(mensagem)
            gravar_log(session, n_processo, mensagem)

    # Retorna a resposta com o resultado do processamento
    return jsonify({"message": "Processos analisados com sucesso."}), 200
        
  
 

def analisa(id_autosprocessos, id_andamento, session, numero_unico):
    """
    Lógica que recebe número único do processo e id do documento e chama
    o robô de análise para gerar o dicionário com todas as informações
    """

    # Função para baixar o pdf no alfresco a partir do número do processo
    path = importar_autos_alfresco(id_autosprocessos)
    
    print("Comecou a analisar")

    if not path:
        print("Processo não encontrado no Alfresco!")
        response = jsonify({"error": "Processo não encontrado no Alfresco!"})
        response.status_code = 400
        return response

    # Função para separar a peça dado o id do documento
    file_path, filename, primeira_pagina = separar_pelo_id(path, id_andamento)

    if file_path is None:
        print("Não foi encontrado um documento com o id especificado!")
        response = jsonify({"error": "Não foi encontrado um documento com o id especificado!"})
        response.status_code = 400
        return response

    # Verificar se o arquivo não está vazio
    with open(file_path, 'rb') as file:
        pdf_content = file.read()

    if len(pdf_content) == 0:
        print("O arquivo enviado está vazio!")
        response = jsonify({"error": "O arquivo enviado está vazio!"})
        response.status_code = 400
        return response

    pdf_filename = filename
    file_path = os.path.join('temp', pdf_filename)

    models = {
        "honorarios": "gpt-4o",
        "doutros": "gpt-4o",
        "medicamentos": "gpt-4o",
        "alimentares": "gpt-4o",
        "internacao": "gpt-4o",
        "resumo": "gpt-4o",
        "geral": "gpt-4o"
    }

    try:
        resposta = AnalisePortaria(file_path, models, pdf_filename, Verbose=False)
    except Exception as e:
        print(f"Erro ao processar: {str(e)}")
        
        #atualizar_status(resultado["id"], session, status=3)
        mensagem = f"Erro na Análise do Processo: Número único {numero_unico} Id {id_autosprocessos} e id documento {id_andamento} - {str(e)}"
        print(mensagem)
        gravar_log(session, numero_unico, mensagem)
        
        response = jsonify({"error": f"Não foi possível analisar o processo {id_autosprocessos} - {str(e)}"})
        response.status_code = 400
        return response

    # Verificar se a resposta não é um dicionário
    if not isinstance(resposta, dict):
        print("O retorno de AnalisePortaria não é um dicionário!")
        response = jsonify({"error": "O retorno de AnalisePortaria não é um dicionário"})
        response.status_code = 400
        return response

    # Adicionar informações à resposta
    resposta['primeira_pagina'] = primeira_pagina + 1

    return resposta



def grava_resultado_BD(id, id_andamento, resultado, session):

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
        possui_outros = :possui_outros,
        possui_outros_impeditivos = :possui_outros_impeditivos,
        possui_condenacao_honorarios = :possui_condenacao_honorarios,  
        possui_danos_morais = :possui_danos_morais, 
        lista_outros = :lista_outros,
        lista_outros_impeditivos = :lista_outros_impeditivos,
        custo_analise = :custo_analise, 
        input_tokens = :input_tokens,
        completion_tokens = :completion_tokens,
        resumo =:resumo, 
        resumo_analise =:resumo_analise,
        marcado_analisar =:marcado_analisar, 
        dt_analisado =:dt_analisado,
        pagina_analisada =:pagina_analisada, 
        id_documento_analisado =:id_analisado,
        houve_extincao = :houve_extincao, 
        cumprimento_de_sentenca = :cumprimento_de_sentenca, 
        bloqueio_de_recursos = :bloqueio_de_recursos,
        monocratica = :monocratica
        WHERE ta.id=:id
    """)

    session.execute(textosql, {
        'id': id,
        'tipo_documento': resultado['tipo_documento'] if 'tipo_documento' in resultado else None,
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
        'possui_outros': resultado['possui_outros'] if 'possui_outros' in resultado else None,
        'possui_outros_impeditivos': resultado['possui_outros_proibidos'] if 'possui_outros_impeditivos' in resultado else None,
        'possui_condenacao_honorarios': resultado['condenacao_honorarios'] if resultado['condenacao_honorarios'] is not None else False,
        'possui_danos_morais': resultado['indenizacao'] if resultado['indenizacao'] is not None else False,
        'respeita_valor_teto': resultado['respeita_valor_teto'] if resultado['respeita_valor_teto'] is not None else False,
        'lista_outros': resultado['lista_outros'] if 'lista_outros' in resultado else None,
        'lista_outros_impeditivos': resultado['lista_outros_proibidos'] if resultado['lista_outros_proibidos'] is not None else None,
        'custo_analise': resultado['custollm'] if 'custollm' in resultado else None,
        'input_tokens': resultado['tokensllm'][0],
        'completion_tokens': resultado['tokensllm'][1] if 'tokensllm' in resultado else None,
        'resumo': resultado['resumo'] if 'resumo' in resultado else None,
        'resumo_analise': resultado['resumo_analise'] if 'resumo_analise' in resultado else None,
        'marcado_analisar': True,
        'dt_analisado': datetime.now(),
        'pagina_analisada': resultado['primeira_pagina'] if 'primeira_pagina' in resultado else None,
        'id_analisado': id_andamento, 
        'houve_extincao': resultado['houve_extincao'] if 'houve_extincao' in resultado else None,
        'cumprimento_de_sentenca': resultado['cumprimento_de_sentenca'] if 'cumprimento_de_sentenca' in resultado else None,
        'bloqueio_de_recursos': resultado['bloqueio_de_recursos'] if 'bloqueio_de_recursos' in resultado else None,
        'monocratica': resultado['monocratica'] if 'monocratica' in resultado else None
    })

    # INSERÇÃO NA TABELA DE MEDICAMENTOS
    for medicamento in resultado['lista_medicamentos']:
        #textosql1 = text("SELECT * from db_pge.scm_robo_intimacao.tb_analiseportaria ta WHERE ta.id_analiseportaria =:id")
        #buscaidportaria = session.execute(textosql1, {'id': id}).fetchone()
        #idportaria = buscaidportaria[0]
        
        buscaultimoid = session.execute(text("SELECT MAX(tm.id) from db_pge.scm_robo_intimacao.tb_medicamentos tm")).fetchone()
        idmedicamento = (buscaultimoid[0] or 1) + 1

        insercaoAM = session.execute(text("""
            INSERT into db_pge.scm_robo_intimacao.tb_medicamentos 
            (id, id_analiseportaria, nome_principio, nome_comercial, dosagem, possui_anvisa, registro_anvisa, fornecido_SUS, valor) 
            values(:id, :id_analiseportaria, :nome_principio, :nome_comercial, :dosagem, :possui_anvisa, :registro_anvisa, :fornecido_SUS, :valor)
        """), {
            'id': idmedicamento,
            'id_analiseportaria': id,
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
        #textosql1 = text("SELECT * from db_pge.scm_robo_intimacao.tb_analiseportaria ta WHERE ta.id_analiseportaria =:id")
        #buscaidportaria = session.execute(textosql1, {'id': id}).fetchone()
        #idportaria = buscaidportaria[0]

        buscaultimoid = session.execute(text("SELECT MAX(tc.id) from db_pge.scm_robo_intimacao.tb_compostos tc")).fetchone()
        idcomposto = (buscaultimoid[0] or 0) + 1  # Incrementa o ID, começando de 1 se vazio

        insercaoAC = session.execute(text("""
            INSERT into db_pge.scm_robo_intimacao.tb_compostos
            (id, id_analiseportaria, nome_composto, qtde, duracao, possui_anvisa, registro_anvisa, valor)
            values(:id, :id_analiseportaria, :nome_composto, :qtde, :duracao, :possui_anvisa, :registro_anvisa, :valor)
        """), {
            'id': idcomposto,
            'id_analiseportaria': id,
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
def captura_ids_processo(id_analiseportaria, id_autosprocessos, id_dado=None, SelecaoAutomaticaDocumento=True):
    path = importar_autos_alfresco(id_autosprocessos)
    if not path:
        print("Processo não encontrado no Alfresco")
        return False

    # Configuração do banco de dados
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Extração das páginas e informações do documento
    pages_to_check = extract_pages_to_check(path)
    document_info = extract_document_info_from_pages(path, pages_to_check)

    # Usa ID fornecido ou consulta o banco
    if id_dado is not None:
        id_analiseportaria = id_dado
    else:
        query = text('''
            SELECT numerounico, id 
            FROM scm_robo_intimacao.tb_analiseportaria ta 
            WHERE ta.id = :id_analiseportaria 
              AND analisado IS NULL
        ''')
        resultado = session.execute(query, {"id_analiseportaria": id_analiseportaria}).mappings().first()

        num_unico = resultado["numerounico"]

        if resultado:
            id_analiseportaria = resultado["id"]
        else:
            session.close()
            if os.path.isfile(path):
                os.remove(path)
            return False

    for dados in document_info:
        try:
            # Desestruturar informações do documento
            id_doc = dados["id_doc"]
            data_assinatura = dados["dt_assinatura"].replace('\n', ' ')
            documento = dados["nome"].replace('\n', ' ')
            tipo = dados["tipo"]

            # Obter o maior ID atual da tabela
            res = session.execute(
                text('SELECT MAX(id) AS valor_max FROM db_pge.scm_robo_intimacao.tb_documentosautos')
            ).mappings().first()
            max_id = (res["valor_max"] or 0) + 1

            # Verificar se o documento já existe
            query_check = text('''
                SELECT numerounico, id_documento 
                FROM db_pge.scm_robo_intimacao.tb_documentosautos 
                WHERE id_analiseportaria = :id_analiseportaria 
                  AND id_documento = :iddocumento
            ''')
            check = session.execute(query_check, {
                "id_analiseportaria": id_analiseportaria,
                "iddocumento": id_doc
            }).mappings().first()

            if not check:
                # Inserir novo documento
                session.execute(text('''
                    INSERT INTO db_pge.scm_robo_intimacao.tb_documentosautos 
                    (id, numerounico, id_documento, dt_assinatura, nome, tipo, id_analiseportaria) 
                    VALUES (:id, :numerounico, :id_documento, :dt_assinatura, :nome, :tipo, :id_analiseportaria)
                '''), {
                    'id': max_id,
                    'numerounico': num_unico,
                    'id_documento': id_doc,
                    'dt_assinatura': data_assinatura,
                    'nome': documento,
                    'tipo': tipo,
                    'id_analiseportaria': id_analiseportaria
                })
        except Exception as e:
            print(f"Erro ao processar {id_analiseportaria}: {e}")
            continue

    session.commit()

    # Seleção automática do documento a ser analisado
    if SelecaoAutomaticaDocumento:
        interesses = ["Petição Inicial", "Decisão", "Sentença", "Interlocutória"]
        forca_peticao = 0
        IdAndamentoPortaria = CheckIdOfInterest(path, document_info, interesses, forca_peticao)

        if IdAndamentoPortaria is not None:
            session.execute(text('''
                UPDATE db_pge.scm_robo_intimacao.tb_analiseportaria
                SET id_documento_analisado = :IdAndamentoPortaria,
                    marcado_analisar = TRUE
                WHERE id = :id_analiseportaria
            '''), {
                'id_analiseportaria': id_analiseportaria,
                'IdAndamentoPortaria': IdAndamentoPortaria
            })
            session.commit()
        else:
            print(f"Erro ao fazer a seleção automática para {id_analiseportaria}")
            
    if os.path.isfile(path):
        os.remove(path)

    return True


#Função para baixar o pdf no alfresco a partir do numero do processo
def importar_autos_alfresco(id_autosprocessos):  
      engine_alfresco = create_engine(DATABASE_URL)
      Session_alfresco = sessionmaker(bind=engine_alfresco)  
      metadata_alfresco = MetaData()
      
      session_alfresco = Session_alfresco()
      query = text('SELECT numerounico, idalfresco,id FROM scm_robo_intimacao.tb_autosprocessos WHERE id = :id')
      resultado_alfresco = session_alfresco.execute(query, {"id": id_autosprocessos}).fetchone()

      id_alfresco =  resultado_alfresco[1]
      id_processo = resultado_alfresco[2]
      
      session_alfresco.commit()

      download_url = f"{alfresco_url}/alfresco/api/-default-/public/alfresco/versions/1/nodes/{id_alfresco}/content"

      path = None
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

#Função que irá separar o documento de id (parametro) a ser analisado pela portaria do restante dos autos 
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






#grava uma mensagem no log do banco de dados
def gravar_log(session, numerounico, mensagem):
    """
    Grava um log na tabela scm_robo_intimacao.tb_log_extracao_robo.

    :param session: Sessão do banco de dados.
    :param numerounico: Identificador único do processo.
    :param mensagem: Mensagem a ser gravada no log.
    """
    
    # Define os valores fixos e o timestamp atual
    base = 'PPRS'
    data_execucao = datetime.now()

    query = '''
        INSERT INTO scm_robo_intimacao.tb_log_extracao_robo (log, data_execucao, base, numerounico)
        VALUES (:log, :data_execucao, :base, :numerounico)
    '''
    params = {
        'log': mensagem,
        'data_execucao': data_execucao,
        'base': base,
        'numerounico': numerounico
    }

    # Executa a consulta e faz o commit
    session.execute(text(query), params)
    session.commit()


#atualiza o status de um processo
def atualizar_status(id, session, status):
    """
    Atualiza o status de um processo em tb_analiseportaria 

    :param id: id do processo.
    :param session: Sessão do banco de dados.
    :param status: Código do status.
    """
    status_map = {
        1: 'Recebido',
        2: 'Em Análise',
        3: 'Analisado',
        4: 'Erro no Recebimento',
        5: 'Erro na Análise'
    }

    status = status_map.get(status)

    if not status:
        print('Não foi possível fazer a atualização do status: Código inválido.')
        return

    query = '''
        UPDATE db_pge.scm_robo_intimacao.tb_analiseportaria
        SET status = :status
        WHERE id = :id
    '''
    params = {'status': status, 'id': id}

    # Executa a consulta e faz o commit
    session.execute(text(query), params)
    session.commit()

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


def encontrar_arquivo(nome_arquivo):
    
    nome_arquivo_comp = f"portaria_temp.pdf"
    diretorio_arquivos = f'temp/'
    for raiz, _, arquivos in os.walk(diretorio_arquivos):
        if nome_arquivo_comp in arquivos:
            caminho_completo = os.path.join(raiz, nome_arquivo_comp)
            return caminho_completo
    return False



# Função para processar PDFs e extrair algumas informações importantes para o contexto de geração de despacho

def process_pdf(file_path, api_key):
    """
    Processa um arquivo PDF para extrair informações específicas.
    """
    
    # Configura o modelo OpenAI através do LangChain
    #llm = OpenAI(model="gpt-4o", temperature=0)
    llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=api_key)

    # Carrega o conteúdo do PDF
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    # Concatena todo o texto do PDF
    full_text = "".join([doc.page_content for doc in documents])

    # Template do prompt para extração
    prompt_template = PromptTemplate(
        input_variables=["text"],
        template=(
            "Você é um jurista especializado em decisões judiciais. Com base no texto a seguir, "
            "extraia as seguintes informações:\n\n"
            "1. Identificação do Despacho: Indicação de que se trata de uma sentença judicial.\n"
            "2. Sentença do mérito: identificar a sentença do mérito, ou seja se é com ou sem mérito.\n"
            "3. Decisão sobre o Pleito/Mérito: Indicação de se o pleito autoral foi julgado procedente "
            "e a decisão antecipatória de tutela foi ratificada.\n"
            "4. Detalhes da internação: Se houver internação, especificar o tipo do Leito ou Tipo de Internação.\n"
            "5. Especificação do Medicamento: Se houver medicamento, especificar o nome do medicamento "
            "e detalhes, como a dosagem. Confirmação de que o medicamento está registrado na ANVISA.\n"
            "6. Especificação da Consulta, exame ou procedimento: Se houver consulta, exame ou procedimento, especificar os detalhes.\n\n"
            "Texto: {text}"
        )
    )

    # Configurar a cadeia
    chain = LLMChain(llm=llm, prompt=prompt_template)

    # Executar o modelo no texto completo
    full_response = chain.run(text=full_text)

    return full_response


def grava_despacho_bd(id, despacho, session, tokens, cost):
    """
    Atualiza o despacho gerado e soma os valores de input_tokens, completion_tokens e custo_analise na tabela.
    """
    query = text('''
        UPDATE db_pge.scm_robo_intimacao.tb_analiseportaria
        SET despacho_gerado = :despacho,
            input_tokens = COALESCE(input_tokens, 0) + :input_tokens,
            completion_tokens = COALESCE(completion_tokens, 0) + :completion_tokens,
            custo_analise = COALESCE(custo_analise, 0) + :cost
        WHERE id = :id;
    ''')
    
    session.execute(query, {
        'despacho': despacho,
        'input_tokens': tokens[0],
        'completion_tokens': tokens[1],
        'cost': cost,
        'id': id
    })
    
    session.commit()



def selecionar_template(resultado_analise):
    tipo_documento = resultado_analise.get('tipo_documento')
    aplicacao_incisos = any(resultado_analise.get('aplicacao_incisos', []))
    internacao = resultado_analise.get('internacao', False)
    consulta_exame_procedimento = resultado_analise.get('possui_consulta', False)
    possui_insumos = resultado_analise.get('possui_outros', False)
    lista_medicamentos = resultado_analise.get('lista_medicamentos', [])
    lista_compostos = resultado_analise.get('lista_compostos', [])
    #houve_extincao = resultado_analise.get('houve_extincao', False)
    #cumprimento_de_sentenca = resultado_analise.get('cumprimento_de_sentenca', False)
    #bloqueio_de_recursos = resultado_analise.get('bloqueio_de_recursos', False)
    
    
    # Mapear templates para diferentes tipos de documentos
    templates = {
        'Sentença': {
            'medicamento': TEMPLATE_SENTENCA_MEDICAMENTO,
            'internacao': TEMPLATE_SENTENCA_INTERNACAO,
            'composto_alimentar': TEMPLATE_SENTENCA_COMPOSTOS,
            'consulta_exame_procedimento': TEMPLATE_SENTENCA_UNIFICADA,
            'insumos': TEMPLATE_SENTENCA_INSUMOS,
        },
        'Decisão Interlocutória': {
            'medicamento': TEMPLATE_DECISAO_MEDICAMENTO,
            'internacao': TEMPLATE_DECISAO_INTERNACAO,
            'composto_alimentar': TEMPLATE_DECISAO_COMPOSTOS,
            'consulta_exame_procedimento': TEMPLATE_DECISAO_UNIFICADA,
            'insumos': TEMPLATE_DECISAO_INSUMOS,
        },
        'Petição Inicial': {
            'medicamento': TEMPLATE_DECISAO_MEDICAMENTO,
            'internacao_aplica': TEMPLATE_DECISAO_INTERNACAO,
            'composto_alimentar_aplica': TEMPLATE_DECISAO_COMPOSTOS,
            'consulta_exame_procedimento': TEMPLATE_DECISAO_UNIFICADA,
            'insumos': TEMPLATE_DECISAO_INSUMOS,
        }
    }

    
    # Verificar o tipo de documento
    if tipo_documento in templates:
        
        # Medicamento
        if len(lista_medicamentos) > 0:
            return {"template": templates[tipo_documento]['medicamento']}
        
        # Internação
        if internacao:
            return {"template": templates[tipo_documento]['internacao']}
            
        # Composto Alimentar
        if len(lista_compostos) > 0:
            return {"template": templates[tipo_documento]['composto_alimentar']}
            
        # Consultas Exames ou Procedimentos
        if consulta_exame_procedimento:
            return {"template": templates[tipo_documento]['consulta_exame_procedimento']}
        
        # Composto Alimentar
        if possui_insumos:
            return {"template": templates[tipo_documento]['insumos']}
            
    # Caso nenhum template seja encontrado
    print('Sem Template')
    return None

def gerar_despacho(id_analiseportaria,session,resultado_analise):

    ### Parte responsável pela  busca no banco de dados:
    # Pesquisa o
    query = text('''
    SELECT 
        ta.id,
        ta.fk_autosprosaude,
        ta.possui_outros,
        ta.possui_medicamentos,
        ta.possui_condenacao_honorarios,
        ta.aplica_portaria,
        ta.numerounico,
        ta.dt_processado,
        ta.houve_extincao,
        ta.cumprimento_de_sentenca,
        ta.bloqueio_de_recursos,
        ta.monocratica
    FROM scm_robo_intimacao.tb_analiseportaria ta
    WHERE ta.id = :id_analiseportaria
    ''')
    
    #resultado = session.execute(query, {"numeroprocesso":n_processo}).fetchone()
    #retorna o resultado como dicionario
    resultado = session.execute(query, {"id_analiseportaria": id_analiseportaria}).mappings().fetchone()
    
    nome_arquivo =  resultado["fk_autosprosaude"]


    dados_json = {
    "Informações da análise do processo": {
        "Nome do Arquivo": f"{nome_arquivo}.pdf",
        "Análise de medicamentos no documento": (
            "Foram detectados medicamentos no documento analisado"
            if resultado["possui_medicamentos"]
            else "Não foram detectados medicamentos no documento analisado"
        ),
        "Condenação por honorários": (
            "Houve condenação por honorários"
            if resultado["possui_condenacao_honorarios"]
            else "Não houve condenação por honorários"
        ),
        "Aplicação da Portaria 01/2017": (
            "Foi verificada a aplicação da Portaria 01/2017"
            if resultado["aplica_portaria"]
            else "Não foi verificada a aplicação da Portaria 01/2017"
        ),
    }
    }


    #Caso seja extinção, bloqueio ou cumprimento, não há necessidade de fazer leitura do documento
    
    # Verificar condições específicas
    """
    if resultado["houve_extincao"]:
        despacho = "R.H. Não é objeto de aplicação da Portaria 01/2017 por se tratar de processo extinto. Encaminhe-se à assessoria para análise."
        grava_despacho_bd(resultado["id"], despacho, session)
        return True

    if resultado["cumprimento_de_sentenca"]:
        despacho = "R.H. Não é objeto de aplicação da Portaria 01/2017 por se tratar de decisão de cumprimento de sentença. Encaminhe-se à assessoria para análise."
        print(f"E por que nao grava o despacho:{despacho}")
        
        grava_despacho_bd(resultado["id"], despacho, session)
        return True
    """
    
    if resultado["bloqueio_de_recursos"]:
        despacho = "R.H. Não é objeto de aplicação da Portaria 01/2017 por haver bloqueio de verbas ou contas. Encaminhe-se à assessoria para análise."
        grava_despacho_bd(resultado["id"], despacho, session)
        return True

    if resultado["monocratica"]:
        despacho = "R.H. Não é objeto de aplicação da Portaria 01/2017 por se tratar de decisão monocrática. Encaminhe-se à assessoria para análise."
        grava_despacho_bd(resultado["id"], despacho, session)
        return True
    
    # Escrever as informações extraídas em um arquivo JSON
    with open('dl_extracted_data.json', mode='w', encoding='utf-8') as file:
        json.dump(dados_json, file, ensure_ascii=False, indent=4)

    print("DataFrame convertido e salvo em formato JSON com sucesso.")
    
    ### Parte responsável pela análise do arquivo pdf 

    caminho_arquivo =  encontrar_arquivo(nome_arquivo)
    if not caminho_arquivo:
        print("Não encontrou o arquivo.")
        return False
    
    
    # Configuração da chave da API GPT 
    env_path = os.path.join(base_directory, 'ambiente.env')
    load_dotenv(env_path)  # Carrega as variáveis de ambiente de .env

    #verifica se a chave do GPT foi encontrada
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY não está definida")
    
    #Extrai as informacoes do documento
    pdf_extracted_data = process_pdf(caminho_arquivo, api_key)
    

    #fname = os.path.basename(caminho_arquivo)

    # Estrutura de dados a ser salva
    data_to_save = [{"File Name": f"{nome_arquivo}.pdf", "Extracted Information": pdf_extracted_data}]
    
    
    # Escrever as informações extraídas em um arquivo JSON
    with open('pdf_extracted_data.json', mode='w', encoding='utf-8') as file:
        json.dump(data_to_save, file, ensure_ascii=False, indent=4)

    print("Informações extraídas salvas no arquivo JSON com sucesso.")
    
    ## Mesclando os json em um só:

    # Carregar os arquivos JSON
    with open('dl_extracted_data.json', 'r', encoding='utf-8') as file1:
        output_dl = json.load(file1)
        
    #print(f"OUTPUT_DL: {output_dl}")

    with open('pdf_extracted_data.json', 'r', encoding='utf-8') as file2:
        pdf_extracted_data = json.load(file2)

    #print(f"PDF_EXTRACTED_DATA: {output_dl}")

    # Criar um dicionário de busca para pdf_extracted_data baseado no "File Name"
    pdf_data_dict = {item['File Name']: item for item in pdf_extracted_data}
    # Mesclar os arquivos com base no nome do arquivo
    merged_data = []

    merged_entry = {**output_dl, **pdf_data_dict}
    merged_data.append(merged_entry)


    # Salvar o arquivo mesclado
    with open('merged_output.json', 'w', encoding='utf-8') as output_file:
        json.dump(merged_data, output_file, ensure_ascii=False, indent=4)

    

    print("Os arquivos foram mesclados com sucesso.")
    print(f"MERGED DATA: {merged_data}")
  
    with open('merged_output.json', 'r', encoding='utf-8') as file3:
        dadosextraidos = json.load(file3)
    
    # Preparar o modelo de LangChain com o template
    #llm = OpenAI(model="gpt-4o", temperature=0)
    llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=api_key)

    # Selecionar o template com base no resultado da análise
    template_selecionado = selecionar_template(resultado_analise)
    

    # Verificar se o template foi encontrado
    if not template_selecionado:
        print("Nenhum template foi selecionado. Operação encerrada.")
        despacho = "R.H. Não foi possível identificar objeto de aplicação da Portaria 01/2017. Encaminhe-se à assessoria para análise."
        grava_despacho_bd(resultado["id"], despacho, session)
        return True
    
    # Extrair e formatar o template como string única
    template = template_selecionado["template"]

    template_string = "\n\n".join([
        template.get("header", ""),
        "\n".join(template.get("instructions", [])),
        template["template"]["Texto Completo"]["description"],
        "\n".join(template["template"]["Texto Completo"]["elements"]),
        "Dados fornecidos: {dados}"
    ])


    print("Chegou ate o despacho")

    # Criar o PromptTemplate diretamente
    prompt_template = PromptTemplate(
        input_variables=["dados"],
        template=f"{template_string}\n\nDados fornecidos: {{dados}}"
    )

    chain = LLMChain(llm=llm, prompt=prompt_template)
    #chain = RunnableSequence([prompt_template, llm])

    # Dados formatados para o modelo
    dados_para_prompt = json.dumps(dadosextraidos, ensure_ascii=False, indent=4)


    with get_openai_callback() as c1:
        try:
            # Gerar o despacho
            despacho_gerado = chain.run(dados=dados_para_prompt)

            # O custo com a API
            cost = c1.total_cost
        
        except Exception as e:
            print(f"Erro ao gerar o despacho: {str(e)}")
            atualizar_status(resultado["id"], session, status=5)
            mensagem = f"Erro na Geração do Despacho: Número único {resultado['numerounico']} e id {resultado['id']} - {str(e)}"
            print(mensagem)
            gravar_log(session, resultado['numerounico'], mensagem)
            raise e  # Relança a exceção para ser tratada em outro nível, se necessário   
    
    #cost = CustoGpt4o(c1.prompt_tokens, c1.completion_tokens)
    tokens = (c1.prompt_tokens, c1.completion_tokens)
    valor = CustoGpt4o(tokens[0], tokens[1])
    #print(valor)
    
    # Salvar o despacho no banco de dados
    grava_despacho_bd(resultado["id"], despacho_gerado, session, tokens, valor)

    print("Despacho gerado e salvo com sucesso.")
    return True
    



    
    
