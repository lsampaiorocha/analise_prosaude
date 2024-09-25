import psycopg2
from psycopg2 import OperationalError
import pandas as pd



host = '192.168.2.64'
database = 'db_pge'
user =  'scm_robo'
password = 'x6ZP&Fc45k(<'

try:
    
    connection = psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password
    )

    cursor = connection.cursor()

    query = "SELECT * FROM scm_robo_intimacao.tb_autosprosaude ta  WHERE ta.processado IS NOT NULL ;"
    cursor.execute(query)
    rows = cursor.fetchall()

    col_names = [desc[0] for desc in cursor.description]  
    
    df = pd.DataFrame(rows, columns = col_names)
    
    pd.set_option('display.max_columns',None)
    
    print(df.head())

except OperationalError as e:
    print(f"Erro ao conectar ao banco de dados: {e}")
        



