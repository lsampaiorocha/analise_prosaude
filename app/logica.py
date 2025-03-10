from flask import request, jsonify
from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, 
    DECIMAL, ForeignKey, text, Numeric, Text
)

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

import traceback

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

import os
import sys

# Função para obter variáveis de ambiente e garantir que todas estão definidas
def get_env_variable(var_name):
    value = os.getenv(var_name)
    if value is None:
        print(f"ERRO: A variável de ambiente '{var_name}' não está definida.")
        sys.exit(1) 
    return value

# Configurações do Banco de Dados
DB_PARAMS = {
    'host': get_env_variable('DB_HOST'),
    'database': get_env_variable('DB_NAME'),
    'user': get_env_variable('DB_USER'),
    'password': get_env_variable('DB_PASSWORD'),
    'port': get_env_variable('DB_PORT'),
}

DATABASE_URL = f"postgresql://{DB_PARAMS['user']}:{DB_PARAMS['password']}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['database']}"

# Configurações do Alfresco
alfresco_url = get_env_variable('ALFRESCO_URL')
username = get_env_variable('ALFRESCO_USERNAME')
password = get_env_variable('ALFRESCO_PASSWORD')
parent_node_id = get_env_variable('ALFRESCO_PARENT_NODE_ID')


#habilitar ou desabilitar a flag do robô no banco
def ligar_desligar(flag=True):
    try:
        # Criar engine e sessão
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Metadados globais
        metadata = MetaData()
        
        # Registrar a tabela tb_status_robos no metadata
        tb_status_robos = Table(
            'tb_status_robos', metadata,
            Column('id', Integer, primary_key=True),
            Column('isativo', Boolean),
            schema='scm_robo_intimacao'
        )

        # Atualizar a flag "isativo" com o valor de `flag`
        update_query = text('''
            UPDATE scm_robo_intimacao.tb_status_robos
            SET isativo = :flag
            WHERE id = (SELECT id FROM scm_robo_intimacao.tb_status_robos WHERE alias = 'PortariaPROSAUDE')
        ''')

        session.execute(update_query, {"flag": flag})
        session.commit()
        
        # Mensagem dinâmica baseada no estado da flag
        mensagem = f"Robô de Análise de Portaria {'habilitado' if flag else 'desabilitado'} com sucesso"
        
        # Gravar log (supondo que esta função exista)
        gravar_log(session, 0, mensagem)

    except SQLAlchemyError as e:
        print(f"Erro ao conectar ao banco de dados: {str(e)}")
        session.rollback()
    finally:
        session.close()



# Função para obter o estado atual do robô
def obter_status_robo():
    try:
        # Criar engine e sessão
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Consulta para obter o valor de "isativo"
        select_query = text('''
            SELECT isativo 
            FROM scm_robo_intimacao.tb_status_robos
            WHERE alias = 'PortariaPROSAUDE'
        ''')

        result = session.execute(select_query).fetchone()
        
        if result is not None:
            return result[0]  # Retorna True ou False
        else:
            return None  # Caso não encontre a entrada

    except SQLAlchemyError as e:
        print(f"Erro ao conectar ao banco de dados: {str(e)}")
        return None
    finally:
        session.close()


#Cria a sessão para conectar ao banco de dados
def criar_session():

    try:
        # Criar engine e sessão
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine, expire_on_commit=False)

        # Metadados globais
        metadata = MetaData()
        # Registrar a tabela tb_autosprosaude no metadata
        tb_autosprocessos = Table(
            'tb_autosprocessos', metadata,
            Column('id', Integer, primary_key=True, server_default=text("nextval('scm_robo_intimacao.tb_autosprocessos_id_seq'::regclass)")),
            Column('numerounico', String, nullable=False),
            Column('dt_inicial', DateTime, nullable=True),
            Column('dt_final', DateTime, nullable=True),
            Column('caminho', String, nullable=True),
            Column('base', String, nullable=True),
            Column('processado', Boolean, nullable=True),
            Column('dt_solicitacao', DateTime, nullable=True),
            Column('dt_processado', DateTime, nullable=True),
            Column('caminhopje1', String, nullable=True),
            Column('processadopje1', Boolean, nullable=True),
            Column('caminhopje2', String, nullable=True),
            Column('processadopje2', Boolean, nullable=True),
            Column('dt_processadopje1', DateTime, nullable=True),
            Column('dt_processadopje2', DateTime, nullable=True),
            Column('caminhoesag1', String, nullable=True),
            Column('processadoesag1', Boolean, nullable=True),
            Column('caminhoesag2', String, nullable=True),
            Column('processadoesag2', Boolean, nullable=True),
            Column('dt_processadoesag1', DateTime, nullable=True),
            Column('dt_processadoesag2', DateTime, nullable=True),
            Column('idalfresco', String, nullable=True),
            Column('setorrequisicao', String, nullable=True),
            Column('avisonoportal', Boolean, nullable=True),
            schema='scm_robo_intimacao'
        )
        
        # Definição da tabela tb_analiseportaria
        tb_analiseportaria = Table(
            'tb_analiseportaria', metadata,
            Column('id', Integer, primary_key=True, server_default=text("nextval('scm_robo_intimacao.tb_analiseportaria_id_seq'::regclass)")),
            Column('fk_autosprosaude', Integer),
            Column('numerounico', String),
            Column('caminho', String),
            Column('base', String),
            Column('dt_processado', DateTime),
            Column('marcado_analisar', Boolean),
            Column('analisado', Boolean),
            Column('id_documento_analisado', String),
            Column('dt_analisado', DateTime),
            Column('tipo_documento', String),
            Column('aplica_portaria', Boolean),
            Column('despacho_gerado', String),
            Column('possui_medicamentos', Boolean),
            Column('possui_internacao', Boolean),
            Column('possui_consultas_exames_procedimentos', Boolean),
            Column('possui_insulina', Boolean),
            Column('possui_insumos', Boolean),
            Column('possui_multidisciplinar', Boolean),
            Column('possui_custeio', Boolean),
            Column('possui_compostos', Boolean),
            Column('possui_condenacao_honorarios', Boolean),
            Column('valor_condenacao_honorarios', Numeric),
            Column('possui_danos_morais', Boolean),
            Column('lista_outros', String),
            Column('input_tokens', Integer),
            Column('completion_tokens', Integer),
            Column('custo_analise', Numeric),
            Column('resumo', Text),
            Column('avaliacao_analise', String),
            Column('pagina_analisada', Integer),
            Column('resumo_analise', String),
            Column('confirma_analise', Boolean),
            Column('possui_outros_impeditivos', Boolean),
            Column('respeita_valor_teto', Boolean),
            Column('possui_outros', Boolean),
            Column('status', String),
            Column('avisadonoportal', Boolean),
            Column('houve_extincao', Boolean),
            Column('cumprimento_de_sentenca', Boolean),
            Column('bloqueio_de_recursos', Boolean),
            Column('monocratica', Boolean),
            Column('lista_outros_impeditivos', String),
            Column('erro_importacao', Boolean, server_default=text("false")),
            Column('erro_analise', Boolean, server_default=text("false")),
            schema='scm_robo_intimacao'
        )
        
        # Definição da tabela atualizada
        tb_documentosautos = Table(
            'tb_documentosautos', metadata,
            Column('id', Integer, primary_key=True, server_default=text("nextval('scm_robo_intimacao.tb_documentosautos_id_seq'::regclass)")),
            Column('numerounico', String),
            Column('id_documento', String),
            Column('dt_assinatura', DateTime),  # Alterado para timestamp sem fuso horário
            Column('nome', String),
            Column('tipo', String),
            Column('id_analiseportaria', Integer),
            schema='scm_robo_intimacao'
        )

        tb_medicamentos = Table(
            'tb_medicamentos', metadata,
            Column('id', Integer, primary_key=True, server_default=text("nextval('scm_robo_intimacao.tb_medicamentos_id_seq'::regclass)")),
            Column('id_analiseportaria', Integer, nullable=True),
            Column('data_analise', DateTime, nullable=True),
            Column('nome_principio', String, nullable=True),
            Column('nome_comercial', String, nullable=True),
            Column('dosagem', Numeric, nullable=True),
            Column('qtde', Integer, nullable=True),
            Column('possui_anvisa', Boolean, nullable=True),
            Column('registro_anvisa', String, nullable=True),
            Column('fornecido_sus', Boolean, nullable=True),
            Column('valor', Numeric, nullable=True),
            schema='scm_robo_intimacao'
        )
        
        
        tb_compostos = Table(
            'tb_compostos', metadata,
            Column('id', Integer, primary_key=True, server_default=text("nextval('scm_robo_intimacao.tb_compostos_id_seq'::regclass)")),
            Column('id_analiseportaria', Integer, nullable=True),
            Column('data_analise', DateTime, nullable=True),
            Column('nome_composto', String, nullable=True),
            Column('qtde', Integer, nullable=True),
            Column('duracao', Integer, nullable=True),
            Column('possui_anvisa', Boolean, nullable=True),
            Column('registro_anvisa', String, nullable=True),
            Column('valor', Numeric, nullable=True),
            schema='scm_robo_intimacao'
        )
        
        session = Session()
        return session
        
    except SQLAlchemyError as e:
        return f"Erro ao conectar ao banco de dados: {str(e)}"
        #return jsonify({"error": "Erro ao conectar ao banco de dados", "details": str(e)}), 500



def importar_processos():
  
    """
    Lógica da Rota para importar os processos de intimações cujos autos já tenham sido baixados pelos
    robô de distribuição de processos (tabela tb_autosprocessos) para a tabela tb_analiseportaria
    """ 

    print("Começou")
    
    session = criar_session()

    if isinstance(session, str):
        return jsonify({"error": "Erro ao conectar ao banco de dados", "details": session}), 500


    # Marcador para ignorar linha
    marca = 0

    # Obter a data limite para os últimos 15 dias
    data_limite = datetime.now() - timedelta(days=15)
    data_limite_str = data_limite.strftime('%Y-%m-%d')  # Formato YYYY-MM-DD

      
    # Consulta inicial para buscar os processos que ainda não estão em tb_analiseportaria
    query = text('''
        SELECT 
            ta.id, 
            ta.numerounico, 
            ta.caminho, 
            ta.base, 
            ta.dt_processado, 
            ta.setorrequisicao
        FROM 
            scm_robo_intimacao.tb_autosprocessos ta
        LEFT JOIN 
            scm_robo_intimacao.tb_analiseportaria ap 
            ON ta.id = ap.fk_autosprosaude
        WHERE 
            ta.processado = true 
            AND Upper(ta.setorrequisicao) = :setor 
            AND ta.base LIKE :base 
            AND ta.avisonoportal = true
            AND ta.dt_processado >= :data_limite
            AND ap.fk_autosprosaude IS NULL
    ''')

    # Executando a consulta com os parâmetros necessários
    resultados = session.execute(query, {
        "setor": "PROSAUDE", 
        "base": "%PJE%", 
        "data_limite": data_limite_str
    }).mappings().fetchall()


    if not resultados:
        print("Nenhum processo novo encontrado.")
        return jsonify({"message": "Nenhum processo novo encontrado."}), 200
    
    print(f"RESULTADOS PARA IMPORTACAO-OK: {resultados}")

    for row in resultados:
        """
        # Verificar se o processo já foi inserido na tabela tb_analiseportaria
        checagem_query = text('''
            SELECT fk_autosprosaude 
            FROM scm_robo_intimacao.tb_analiseportaria ta 
            WHERE ta.fk_autosprosaude = :fk_autosprosaude
        ''')
        checagem = session.execute(checagem_query, {"fk_autosprosaude": row["id"]}).fetchone()
        
        print(f"CHECAGEM-O PARA {row['numerounico']}: {checagem} : {row}")

        if checagem:
            print(f"Ignorado: Processo de número único {row['numerounico']} e id {row['id']} já foi inserido.")
            continue

        """

        # Preparar os dados para inserção
        dados_insercao = {
            "fk_autosprosaude": row["id"],
            "numerounico": row["numerounico"],
            "caminho": row["caminho"],
            "base": row["base"],
            "dt_processado": row["dt_processado"]
        }

        # Inserir o novo processo na tabela tb_analiseportaria
        insercao_query = text('''
            INSERT INTO scm_robo_intimacao.tb_analiseportaria 
            (fk_autosprosaude, numerounico, caminho, base, dt_processado) 
            VALUES (:fk_autosprosaude, :numerounico, :caminho, :base, :dt_processado)
            RETURNING id
        ''')

        
        mensagem = f"[importar_processos] Iniciando importação: Processo de número único {row['numerounico']} e id {row['id']}."
        print(mensagem)
        gravar_log(session, row['numerounico'], mensagem)
        
        # Executa a inserção e captura o ID gerado automaticamente
        try:
            result = session.execute(insercao_query, dados_insercao)
            novo_id = result.scalar()  # Captura o novo ID gerado
            session.commit()  # Confirma a transação
            print(f"ID gerado: {novo_id}")
        except Exception as e:
            print(f"Erro ao inserir o processo: {e}")
            session.rollback()  # Reverte a transação em caso de erro
            continue


        print(f"Analisando Documentos dos Autos: Processo de número único {row['numerounico']} e id {row['id']}.")

        # Capturar documentos relacionados ao processo
        c = captura_ids_processo(novo_id, row["id"], row["numerounico"], session, id_dado=None, SelecaoAutomaticaDocumento=True)

        if not c:
            mensagem = f"[importar_processos] Erro ao Analisar Documentos dos Autos: Processo de número único {row['numerounico']} e id {row['id']}."
            # Atualizar o status do processo
            gravar_log(session, row['numerounico'], mensagem)
            registrar_erro(session, novo_id, tipo_erro=1)
            atualizar_status(novo_id, session=session, status=1)
            
            print(mensagem)
            continue

        mensagem = f"[importar_processos] Importado com sucesso: Processo de número único {row['numerounico']} e id {row['id']}."
        print(mensagem)
        gravar_log(session, row['numerounico'], mensagem)

        # Atualizar o status do processo
        atualizar_status(novo_id, session=session, status=1)

    # Confirmar transações pendentes
    session.commit()

    print("Processamento concluído.")
    return jsonify({"message": "Processos importados com sucesso."}), 200

    

   
def analisar_marcados():
    """
    Lógica da Rota para analisar todos os processos da tabela tb_analiseportaria tais que:
    - não tenham sido ainda analisados
    - estejam marcados para análise 
    - possuam o campo id_documento definido
    """

    
    session = criar_session()

    if isinstance(session, str):
        return jsonify({"error": "Erro ao conectar ao banco de dados", "details": session}), 500

    
    
    

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
    resultados = session.execute(query).mappings().fetchall()
    
    
    mensagem = f"[ANALISAR_MARCADOS] Iniciando a Análise de processos marcados. Existem {len(resultados)} processos marcados para análise"
    print(f"Processos marcados para analise {resultados}")
    gravar_log(session, 0, mensagem)

    # Iterar pelos resultados
    for resultado in resultados:
        n_processo = resultado["numerounico"]
        print(n_processo)

        id_andamento = resultado["id_documento_analisado"]
        atualizar_status(resultado["id"], session, status=2)
        mensagem = f"[analisar_marcados] Iniciando Análise do processo: Número único {resultado['numerounico']} e id {resultado['id']}"
        gravar_log(session, resultado["numerounico"], mensagem)


        if id_andamento is not None:
            resposta = analisa(resultado["fk_autosprosaude"], id_andamento, session, n_processo)
            print(id_andamento)
        else:
            resposta = "Não foi identificado o id do documento a analisar"  
                        
        mensagem = f"[analisar_marcados] Resposta da analise: Número único {resultado['numerounico']} e id {resultado['id']} Resposta {str(resposta)}"
        print(mensagem)
        gravar_log(session, resultado["numerounico"], mensagem)

        # Verificar se a resposta é um dicionário
        if isinstance(resposta, dict):
            if "error" in resposta:
                atualizar_status(resultado["id"], session, status=3)
                registrar_erro(session, resultado["id"], tipo_erro=2)
                mensagem = f"[analisar_marcados] Erro na Análise do Processo: Número único {n_processo} e id {resultado['id']} - {resposta['error']}"
                print(mensagem)
                gravar_log(session, n_processo, mensagem)
                grava_analise_fracassada(resultado["id"], id_andamento, session)
            else:  # sucesso
                grava_resultado_BD(resultado["id"], id_andamento, resposta, session)
                
                mensagem = f"[analisar_marcados] Iniciando elaboração do Despacho: Número único {n_processo} e id {resultado['id']}"
                print(mensagem)
                gravar_log(session, n_processo, mensagem)
                
                gerar_despacho(resultado["id"], session, resposta)
                
                atualizar_status(resultado["id"], session, status=3)
                mensagem = f"[analisar_marcados] Sucesso na Análise do Processo: Número único {n_processo} e id {resultado['id']}"
                print(mensagem)
                gravar_log(session, n_processo, mensagem)
        else:
            # Caso a resposta não seja um dicionário, trate como erro inesperado
            atualizar_status(resultado["id"], session, status=3)
            registrar_erro(session, resultado["id"], tipo_erro=2)
            erro = resposta.get_json() if hasattr(resposta, "get_json") else str(resposta)
            mensagem = f"Erro inesperado na Análise do Processo: Número único {n_processo} e id {resultado['id']} - {erro}"
            print(mensagem)
            gravar_log(session, n_processo, mensagem)
            grava_analise_fracassada(resultado["id"], id_andamento, session)

    # Retorna a resposta com o resultado do processamento
    return jsonify({"message": "Processos analisados com sucesso."}), 200


 

def analisa(id_autosprocessos, id_andamento, session, numero_unico):
    """
    Lógica que recebe número único do processo e id do documento e chama
    o robô de análise para gerar o dicionário com todas as informações
    """

    # Função para baixar o pdf no alfresco a partir do número do processo
    (path, alfresco) = importar_autos_alfresco(id_autosprocessos, numero_unico)
    

    if not path:
        mensagem = f"[analisa] Processo não encontrado no Alfresco: Número único {numero_unico}"
        print(mensagem)
        gravar_log(session, numero_unico, mensagem)
        response = jsonify({"error": "Processo não encontrado no Alfresco!"})
        response.status_code = 400
        return response

    # Função para separar a peça dado o id do documento
    file_path, filename, primeira_pagina = separar_pelo_id(path, id_andamento)

    if file_path is None:
        mensagem = f"[analisa] Não foi encontrado um documento com o id especificado: Número único {numero_unico} Id Andamento {id_andamento}"
        print(mensagem)
        gravar_log(session, numero_unico, mensagem)
        response = jsonify({"error": "Não foi encontrado um documento com o id especificado!"})
        response.status_code = 400
        return response

    # Verificar se o arquivo não está vazio
    with open(file_path, 'rb') as file:
        pdf_content = file.read()

    if len(pdf_content) == 0:
        mensagem = f"[analisa] O documento está vazio: Número único {numero_unico} Id Andamento {id_andamento}"
        print(mensagem)
        gravar_log(session, numero_unico, mensagem)
        response = jsonify({"error": "O documento está vazio"})
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
        mensagem = f"[analisa] Erro na Análise do Processo: Número único {numero_unico} Id {id_autosprocessos} e id documento {id_andamento} - {str(e)}"
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



#Grava o resultado da análise no BD
def grava_resultado_BD(id, id_andamento, resultado, session):
    
    
    
    # Resolve erros que estavam ocorrendo de ids duplicados
    session.execute(text('''
        SELECT setval(
            'scm_robo_intimacao.tb_medicamentos_id_seq', 
            (SELECT COALESCE(max(id), 1) FROM scm_robo_intimacao.tb_medicamentos)
        )
    '''))
 
    session.execute(text('''
        SELECT setval(
            'scm_robo_intimacao.tb_compostos_id_seq', 
            (SELECT COALESCE(max(id), 1) FROM scm_robo_intimacao.tb_compostos)
        )
    '''))
    
    session.execute(text('''
        SELECT setval(
            'scm_robo_intimacao.tb_analiseportaria_id_seq', 
            (SELECT COALESCE(max(id), 1) FROM scm_robo_intimacao.tb_analiseportaria)
        )
    '''))
    
    session.commit()  # Garante que as sequências sejam atualizadas imediatamente

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
        
        # Inserção na tabela tb_medicamentos
        insercaoAM = session.execute(text("""
            INSERT INTO db_pge.scm_robo_intimacao.tb_medicamentos 
            (id_analiseportaria, nome_principio, nome_comercial, dosagem, possui_anvisa, registro_anvisa, fornecido_SUS, valor) 
            VALUES (:id_analiseportaria, :nome_principio, :nome_comercial, :dosagem, :possui_anvisa, :registro_anvisa, :fornecido_SUS, :valor)
        """), {
            'id_analiseportaria': int(id) if id is not None else None,
            'nome_principio': medicamento.get('nome_principio', 'Desconhecido'),  # Valor padrão 'Desconhecido'
            'nome_comercial': medicamento.get('nome_comercial', 'Desconhecido'),  # Valor padrão 'Desconhecido'
            'dosagem': int(medicamento.get('dosagem', 0)),  # Valor padrão 0 para dosagem
            'possui_anvisa': bool(medicamento.get('registro_anvisa')),  # Se tiver registro, assume True
            'registro_anvisa': str(medicamento.get('registro_anvisa', '')),  # Valor padrão vazio para registro
            'fornecido_SUS': bool(medicamento.get('oferta_SUS', False)),  # Valor padrão False para fornecido pelo SUS
            'valor': float(str(medicamento.get('preco_PMVG', '0')).replace('R$', '').strip())  # Valor padrão 0.0
        })

        
    
    # INSERÇÃO NA TABELA DE COMPOSTOS ALIMENTARES
    for alimento in resultado.get('lista_compostos', []):  # Garante lista vazia se não existir a chave
    
        insercaoAC = session.execute(text("""
            INSERT INTO db_pge.scm_robo_intimacao.tb_compostos
            (id_analiseportaria, nome_composto, qtde, duracao, possui_anvisa, registro_anvisa, valor)
            VALUES (:id_analiseportaria, :nome_composto, :qtde, :duracao, :possui_anvisa, :registro_anvisa, :valor)
        """), {
            'id_analiseportaria': int(id) if id is not None else None,
            'nome_composto': alimento.get('nome', 'Desconhecido'),  # Valor padrão seguro
            'qtde': int(alimento.get('quantidade', 0)),  # Garante valor numérico
            'duracao': int(alimento.get('duracao', 0)),  # Garante valor padrão 0
            'possui_anvisa': bool(alimento.get('possui_anvisa', False)),  # Garante boolean False
            'registro_anvisa': str(alimento.get('registro_anvisa', '')),  # Garante string vazia
            'valor': float(str(alimento.get('valor', '0')).replace('R$', '').replace(',', '.').strip())  # Garante float
        })

    
    #Ao final grava tudo
    session.commit()




#Grava o resultado de uma análise fracassada no BD
def grava_analise_fracassada(id, id_andamento, session):

    # ATUALIZAÇÃO COM OS RESULTADOS DA ANÁLISE
    textosql = text("""
        UPDATE db_pge.scm_robo_intimacao.tb_analiseportaria ta 
        SET tipo_documento = :tipo_documento, 
            analisado = :analisado, 
            aplica_portaria = :aplica_portaria, 
            marcado_analisar = :marcado_analisar, 
            dt_analisado = :dt_analisado,
            pagina_analisada = :pagina_analisada, 
            id_documento_analisado = :id_analisado,
            despacho_gerado = :despacho
        WHERE ta.id = :id
    """)
    
    # Mensagem de despacho
    despacho_fracassado = (
        "R.H. Não foi possível analisar a aplicação da Portaria 01/2017. "
        "Encaminhe-se à assessoria para análise."
    )

    session.execute(textosql, {
        'id': id,
        'tipo_documento': None,
        'analisado': True,
        'aplica_portaria': False,
        'marcado_analisar': True,
        'dt_analisado': datetime.now(),
        'pagina_analisada': None,
        'id_analisado': id_andamento,
        'despacho': despacho_fracassado,
    })
    
    session.commit()




# Captura os ids dos documentos e suas informações a partir de um processo (e o id, pois podem haver vários processos com o mesmo numerounico)
# Preenche essas informações no banco de dados tabela tb_documentos
def captura_ids_processo(id_analiseportaria, id_autosprocessos, numero_unico, session, id_dado=None, SelecaoAutomaticaDocumento=True):
    
    try:
    
        (path, alfresco) = importar_autos_alfresco(id_autosprocessos, numero_unico)
        
        if not path:
            gravar_log(session, numero_unico, f"[captura_ids_processo] Erro: Caminho do arquivo não retornado para ID {id_autosprocessos}")
            return False

        if not os.path.exists(path):
            gravar_log(session, numero_unico, f"[captura_ids_processo] Erro: Arquivo não encontrado - {path}")
            return False

        if os.path.getsize(path) == 0:
            gravar_log(session, numero_unico, f"[captura_ids_processo] Erro: Arquivo está vazio - {path}")
            return False

        # Configuração do banco de dados
        #engine = create_engine(DATABASE_URL)
        #Session = sessionmaker(bind=engine)
        #session = Session()

        # Seleciona apenas as páginas que formam a lista de documentos no início do processo
        pages_to_check = extract_pages_to_check(path)
        #Extrai as informações dos documentos contidas na lista
        document_info = extract_document_info_from_pages(path, pages_to_check)



        # Resolve erro misterioso do id duplicado
        session.execute(text('''
            SELECT setval(
                'scm_robo_intimacao.tb_documentosautos_id_seq', 
                (SELECT COALESCE(max(id), 1) FROM scm_robo_intimacao.tb_documentosautos)
            )
        '''))
        session.commit()  # Garante que a sequência seja atualizada imediatamente


        # Usa ID fornecido ou consulta o banco
        #TODO: VERIFICAR SE E NECESSARIO ESSA PARTE
        if id_dado is not None:
            id_analiseportaria = id_dado
        else:
            #TODO: E ESSA
            query = text('''
                SELECT numerounico, id 
                FROM scm_robo_intimacao.tb_analiseportaria ta 
                WHERE ta.id = :id_analiseportaria 
                AND analisado IS NULL
            ''')
            resultado = session.execute(query, {"id_analiseportaria": id_analiseportaria}).mappings().first()

            if resultado:
                num_unico = resultado["numerounico"]
                id_analiseportaria = resultado["id"]
            else:
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
                        (numerounico, id_documento, dt_assinatura, nome, tipo, id_analiseportaria) 
                        VALUES (:numerounico, :id_documento, :dt_assinatura, :nome, :tipo, :id_analiseportaria)
                    '''), {
                        'numerounico': num_unico,
                        'id_documento': id_doc,
                        'dt_assinatura': data_assinatura,
                        'nome': documento,
                        'tipo': tipo,
                        'id_analiseportaria': id_analiseportaria
                    })
                    
            except Exception as e:
                print(f"Erro ao processar {id_analiseportaria}: {e}")
                session.rollback()  # Faz o rollback em caso de erro
                continue

        session.commit()  # Realiza o commit apenas se tudo estiver OK


        # Seleção automática do documento a ser analisado
        if SelecaoAutomaticaDocumento:
            #Configura os nomes dos documentos de interesse a serem buscados nos autos
            interesses = ["Petição Inicial", "Decisão", "Despacho", "Sentença", "Interlocutória", "Acórdão"]
            
            IdAndamentoPortaria = None
            
            try:
                IdAndamentoPortaria = encontra_id_documento_analise(path, document_info, interesses)
            except Exception as e:
                mensagem = f"[captura_ids_processo] Erro ao fazer a seleção automática para {id_analiseportaria}: {e}"
                gravar_log(session, numero_unico, mensagem)

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
                gravar_log(session, numero_unico, f"[captura_ids_processo] Erro: Não foi possível selecionar o documento automaticamente para número único {numero_unico} Id {id_autosprocessos}")
                grava_analise_fracassada(id=id_analiseportaria, id_andamento=None, session=session)
                
        if os.path.isfile(path):
            os.remove(path)

        return True
    except Exception as e:
        error_trace = traceback.format_exc()  # Captura a stack trace do erro
        gravar_log(session, numero_unico, f"[captura_ids_processo] Falha crítica: {str(e)}\nStack Trace:\n{error_trace}")
        return False


#Função para baixar o pdf no alfresco a partir do numero do processo
def importar_autos_alfresco(id_autosprocessos, numero_unico):  
    engine_alfresco = create_engine(DATABASE_URL)
    Session_alfresco = sessionmaker(bind=engine_alfresco)  
    metadata_alfresco = MetaData()
      
    session_alfresco = Session_alfresco()
    query = text('SELECT numerounico, idalfresco,id FROM scm_robo_intimacao.tb_autosprocessos WHERE id = :id')
    resultado_alfresco = session_alfresco.execute(query, {"id": id_autosprocessos}).fetchone()
    

    if not resultado_alfresco or not resultado_alfresco[1]:
        mensagem = f"[importar_autos_alfresco] Processo não encontrado em tb_autosprocessos: Número único {numero_unico} Resultado Consulta Alfresco {resultado_alfresco}"
        gravar_log(session_alfresco, numero_unico, mensagem)
        print(mensagem)
        session_alfresco.close()
        return (None, None)


    id_alfresco =  resultado_alfresco[1]
    id_processo = resultado_alfresco[2]
    
    session_alfresco.commit()

    download_url = f"{alfresco_url}/alfresco/api/-default-/public/alfresco/versions/1/nodes/{id_alfresco}/content"

    path = None
    try:
        response = requests.get(download_url, auth=HTTPBasicAuth(username, password))
        
        mensagem = f"[importar_autos_alfresco] Requisitado arquivo Alfresco: Número único {resultado_alfresco[0]} Id processo {id_processo} Status Code: {response.status_code} Response Headers: {response.headers} Tamanho da resposta: {len(response.content)} bytes Path Alfresco {download_url}"
        gravar_log(session_alfresco, resultado_alfresco[0], mensagem)        
        
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
                mensagem = f"[importar_autos_alfresco] [DEBUG] Erro ao ler o arquivo: Número único {numero_unico}, Content-Type: {response.headers.get('Content-Type')}"
                gravar_log(session_alfresco, numero_unico, mensagem)
                return (None, download_url)
            
            #cria a pasta arquivos caso nao exista
            os.makedirs("arquivos", exist_ok=True)
            
            path = f"arquivos/{id_processo}.{file_extension}"
            try:
                with open(path, 'wb') as file:
                    file.write(response.content)

                # Verifica o tamanho real do arquivo salvo
                saved_size = os.path.getsize(path)
                mensagem = f"[importar_autos_alfresco] [DEBUG] Arquivo salvo em {path}, tamanho final: {saved_size} bytes"
                gravar_log(session_alfresco, numero_unico, mensagem)
                print(mensagem)

                if saved_size == 0:
                    raise IOError(f"ERRO: O arquivo foi salvo, mas está vazio! Path: {path}")

            except IOError as e:
                print(f"ERRO AO SALVAR O ARQUIVO: {e}")
                mensagem = f"[importar_autos_alfresco] [DEBUG] Ocorreu um erro ao salvar o arquivo {path}, Erro: {e}"
                gravar_log(session_alfresco, numero_unico, mensagem)
                
                return (None, download_url)

                
        else:
            mensagem = f"[importar_autos_alfresco] Processo não encontrado no Alfresco: Número único {resultado_alfresco[0]} Path Alfresco {download_url}"
            print(mensagem)
            gravar_log(session_alfresco, resultado_alfresco[0], mensagem)
            print(mensagem)
            session_alfresco.close()
            return (None, download_url)
        
    except Exception as e:
        print("Erro no download do arquivo: ", e)
        mensagem = f"[importar_autos_alfresco] Erro no download dos autos: Número único {numero_unico} Path Alfresco {download_url} Erro {e}"
        gravar_log(session_alfresco, numero_unico, mensagem)
    
        
        return (None, download_url)
    
    session_alfresco.close()
    return (path, download_url)       

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

    #Cria a pasta  temp caso ela nao exista
    output_path = "temp"
    os.makedirs(output_path, exist_ok=True)
    
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



def registrar_erro(session, id_analiseportaria, tipo_erro):
    """
    Atualiza o campo erro_importacao ou erro_analise na tabela tb_analiseportaria.

    :param session: Sessão do banco de dados.
    :param id_analiseportaria: ID da análise a ser atualizada.
    :param tipo_erro: Código do erro (1 = erro de importação, 2 = erro de análise).
    """

    if not id_analiseportaria:
        print("Erro: ID da análise não pode ser nulo.")
        return False

    if tipo_erro == 1:
        campo = "erro_importacao"
    elif tipo_erro == 2:
        campo = "erro_analise"
    else:
        print("Erro: tipo_erro inválido. Use 1 (importação) ou 2 (análise).")
        return False

    query = text(f"""
        UPDATE scm_robo_intimacao.tb_analiseportaria
        SET {campo} = TRUE
        WHERE id = :id_analiseportaria
    """)

    session.execute(query, {"id_analiseportaria": id_analiseportaria})
    session.commit()

    return True




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
    
    try:
        session.execute(query, {
            'despacho': despacho or "",
            'input_tokens': int(tokens[0]) if tokens and len(tokens) > 0 else 0,
            'completion_tokens': int(tokens[1]) if tokens and len(tokens) > 1 else 0,
            'cost': float(cost) if cost is not None else 0.0,
            'id': int(id) if id is not None else 0
        })
        
        session.commit()
        print(f"Despacho gravado com sucesso para o ID {id}")
        
    except Exception as e:
        print(f"Erro ao gravar despacho no banco de dados: {e}")
        session.rollback()





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
        #despacho = "R.H. Não é objeto de aplicação da Portaria 01/2017 por haver bloqueio de verbas ou contas. Encaminhe-se à assessoria para análise."
        despacho = "R.H. Não é objeto de aplicação da Portaria 01/2017. Encaminhe-se à assessoria para análise."
        grava_despacho_bd(resultado["id"], despacho, session, (0, 0), 0)
        return True

    if resultado["monocratica"]:
        #despacho = "R.H. Não é objeto de aplicação da Portaria 01/2017 por se tratar de decisão monocrática. Encaminhe-se à assessoria para análise."
        despacho = "R.H. Não é objeto de aplicação da Portaria 01/2017. Encaminhe-se à assessoria para análise."
        grava_despacho_bd(resultado["id"], despacho, session, (0, 0), 0)
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
        grava_despacho_bd(resultado["id"], despacho, session, (0, 0), 0)
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
            #atualizar_status(resultado["id"], session, status=3)
            mensagem = f"Erro na Geração do Despacho: Número único {resultado['numerounico']} e id {resultado['id']} - {str(e)}"
            print(mensagem)
            gravar_log(session, resultado['numerounico'], mensagem)
            
            despacho = "R.H. Não foi possível elaborar o despacho de aplicação da Portaria 01/2017. Encaminhe-se à assessoria para análise."
            grava_despacho_bd(resultado["id"], despacho, session, (0, 0), 0)
            
            #raise e  
    
    #cost = CustoGpt4o(c1.prompt_tokens, c1.completion_tokens)
    tokens = (c1.prompt_tokens, c1.completion_tokens)
    valor = CustoGpt4o(tokens[0], tokens[1])
    #print(valor)
    
    # Salvar o despacho no banco de dados
    grava_despacho_bd(resultado["id"], despacho_gerado, session, tokens, valor)

    print("Despacho gerado e salvo com sucesso.")
    return True
    



    
    
