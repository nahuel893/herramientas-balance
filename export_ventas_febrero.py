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

# Query para extraer ventas de febrero 2026
query = '''
    SELECT *
    FROM silver.fact_ventas
    WHERE fecha_comprobante >= '2026-02-01'
      AND fecha_comprobante < '2026-03-01'
    ORDER BY fecha_comprobante, id
'''

print('Extrayendo datos de fact_ventas (febrero 2026)...')
df = pd.read_sql(query, conn)
conn.close()

print(f'Registros obtenidos: {len(df):,}')
print(f'Columnas: {len(df.columns)}')

# Exportar a CSV
output_path = 'fact_ventas_febrero_2026.csv'
print(f'Exportando a CSV: {output_path}')
df.to_csv(output_path, index=False, encoding='utf-8-sig', sep=';')
print('¡Exportación completada!')
