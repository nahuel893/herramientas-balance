import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Configuración de conexión
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)

# Query para extraer raw_sales de bronze
query = '''
    SELECT *
    FROM bronze.raw_sales
'''

print('Extrayendo datos de bronze.raw_sales...')
df = pd.read_sql(query, conn)
conn.close()

print(f'Registros obtenidos: {len(df):,}')
print(f'Columnas: {len(df.columns)}')

# Exportar a CSV
output_path = 'raw_sales_bronze.csv'
print(f'Exportando a CSV: {output_path}')
df.to_csv(output_path, index=False, encoding='utf-8-sig', sep=';')
print('¡Exportación completada!')
