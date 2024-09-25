from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, DECIMAL, ForeignKey, text, schema
from sqlalchemy.orm import sessionmaker   

# Configuração dos parâmetros de conexão
DB_PARAMS = {
    'host': '192.168.2.64',
    'database': 'db_pge',
    'user': 'scm_robo',
    'password': 'x6ZP&Fc45k(<',
    'port': '5432'
}

# Montar a string de conexão
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

# Função para criar o schema se não existir
def criar_schema_scm_robo_portaria():
    with engine.connect() as conn:  # Conectar ao banco de dados
        try:
            # Verificar se o schema existe
            if not engine.dialect.has_schema(conn, 'scm_robo_portaria'):
                conn.execute(schema.CreateSchema('scm_robo_portaria'))  # Criar schema se não existir
            print("Schema 'scm_robo_portaria' verificado/criado com sucesso!")
        except Exception as e:
            print(f"Erro ao criar/verificar o schema: {e}")


# Função para criar a tabela tb_analiseportaria no schema scm_robo_portaria
def criar_tabela_tb_analiseportaria():
    # Definir a estrutura da tabela
    tb_analiseportaria = Table('tb_analiseportaria', metadata,
        Column('id', Integer, primary_key=True),  # Chave primária
        Column('fk_autosprosaude', Integer, ForeignKey('scm_robo_intimacao.tb_autosprosaude.id')),  # FK para tb_autosprosaude no schema scm_robo_intimacao
        Column('numerounico', String),  # Varchar
        Column('caminho', String),  # Varchar
        Column('base', String),  # Varchar
        Column('dt_processado', DateTime),  # Timestamp
        Column('analisado', Boolean),  # Boolean
        Column('resumo', String),  # Varchar
        Column('tipo_documento', Integer),  # Inteiro 1, 2, ou 3
        Column('aplica_portaria', Boolean),  # Boolean
        Column('possui_medicamentos', Boolean),  # Boolean
        Column('possui_internacao', Boolean),  # Boolean
        Column('possui_consultas_exames_procedimentos', Boolean),  # Boolean
        Column('possui_insulina', Boolean),  # Boolean
        Column('possui_insumos', Boolean),  # Boolean
        Column('possui_multidisciplinar', Boolean),  # Boolean
        Column('possui_custeio', Boolean),  # Boolean
        Column('possui_compostos', Boolean),  # Boolean
        Column('possui_condenacao_honorarios', Boolean),  # Boolean
        Column('valor_condenacao_honorarios', DECIMAL(10, 2)),  # Decimal com duas casas
        Column('possui_danos_morais', Boolean),  # Boolean
        Column('lista_outros', String),  # Varchar
        Column('input_tokens', Integer),  # Integer
        Column('completion_tokens', Integer),  # Integer
        Column('custo_analise', DECIMAL(10, 2)),  # Decimal com duas casas
        schema='scm_robo_portaria'  # Especificar o schema
    )

    # Criar a tabela
    metadata.create_all(engine)
    print("Tabela 'tb_analiseportaria' criada com sucesso no schema 'scm_robo_portaria'.")


# Função para criar a tabela tb_medicamentos no schema scm_robo_portaria
def criar_tabela_tb_medicamentos():
    # Definir a estrutura da tabela
    tb_medicamentos = Table('tb_medicamentos', metadata,
        Column('id', Integer, primary_key=True),  # Chave primária
        Column('id_analiseportaria', Integer, ForeignKey('scm_robo_portaria.tb_analiseportaria.id')),  # FK para tb_analiseportaria
        Column('data_analise', DateTime),  # Timestamp
        Column('nome_principio', String),  # Varchar
        Column('nome_comercial', String),  # Varchar
        Column('dosagem', Integer),  # Inteiro
        Column('qtde', Integer),  # Inteiro
        Column('possui_anvisa', Boolean),  # Boolean
        Column('registro_anvisa', String),  # Varchar
        Column('fornecido_sus', Boolean),  # Boolean
        Column('valor', DECIMAL(10, 2)),  # Decimal com duas casas
        schema='scm_robo_portaria'  # Especificar o schema
    )

    # Criar a tabela
    metadata.create_all(engine)
    print("Tabela 'tb_medicamentos' criada com sucesso no schema 'scm_robo_portaria'.")



# Exemplo de uso
if __name__ == "__main__":
    criar_schema_scm_robo_portaria()
    criar_tabela_tb_analiseportaria()
    criar_tabela_tb_medicamentos()