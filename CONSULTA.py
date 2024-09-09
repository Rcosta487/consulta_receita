

# # Importação dos módulos e bibliotecas necessários
import os
import re
from tqdm import tqdm
import selenium
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
servico=Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()

import time
from calendar import monthrange
from datetime import date, timedelta
from datetime import datetime
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

import pyodbc
from tqdm import tqdm

import mysql.connector as mysql

from sqlalchemy import create_engine

import pymysql

data_atual = date.today().strftime('%Y-%m-%d')
# primeiro_dia_mes=(data_atual.replace(day=1)).strftime('%Y-%m-%d')
timeout_segundos = 10

server = os.getenv('SERVIDORSQL')
database = 'SCF'
username = os.getenv('USERSQL')
password = os.getenv('SENHASQL')
cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server +
                      ';DATABASE='+database+';UID='+username+';PWD=' + password)
cursor = cnxn.cursor()



conexaomysql = mysql.connect(
     host='localhost',
     user='root',
     password=os.getenv('USERMYSQL'),
     database='cobranca',
     )

cursormysql=conexaomysql.cursor()
senhamysql=os.getenv('SENHAMYSQL')
#%%

sqlEngine       = create_engine(f'mysql+pymysql://root:{senhamysql}@127.0.0.1/cobranca', pool_recycle=3600)
dbConnection    = sqlEngine.connect()

CONSULTADOS           = pd.read_sql("""select * from cobranca.situacaocpf """
, dbConnection);



REGISTROS          = pd.read_sql("""select * from cobranca.basecfc """
, dbConnection);



download_dir =r"C:\Users\rafaelsantos\Downloads\OBITOS"
default_filename = "Comprovante de Situação Cadastral no CPF.pdf"
#%%

REGISTROS['NASCIMENTO'] = pd.to_datetime(REGISTROS['NASCIMENTO'], errors='coerce')
REGISTROS['NASCIMENTO'] = REGISTROS['NASCIMENTO'].dt.strftime('%d-%m-%Y')

REGISTROS = REGISTROS.loc[REGISTROS['REGIONAL']=='MS']
REGISTROS = REGISTROS[~REGISTROS['CPF'].isin(CONSULTADOS['CPF'])].reset_index(drop=True)
REGISTROS = REGISTROS.loc[REGISTROS['NASCIMENTO'].notna()]


# In[10]:

chrome_prefs = {
    "printing.print_preview_sticky_settings.appState": '{"version":2,"isGcpPromoDismissed":false,"selectedDestinationId":"Save as PDF","recentDestinations":[{"id":"Save as PDF","origin":"local","account":"_"}],"selectedDestinationsSettings":{}}',
    "savefile.default_directory": r"C:\Users\rafaelsantos\Downloads\OBITOS"
}
options.add_experimental_option("prefs", chrome_prefs)
options.add_argument('--kiosk-printing')

options.add_argument("--headless")  # Ativar o modo headless
options.add_argument("--disable-gpu")  # Necessário para o modo headless no Windows
options.add_argument("--no-sandbox")  # Recomendado para o modo headless
options.add_argument("--disable-dev-shm-usage")  # Melhorar o desempenho no modo headless
navegador = webdriver.Chrome(service=servico, options=options)
navegador.get(f'https://servicos.receita.fazenda.gov.br/servicos/cpf/consultasituacao/ConsultaPublica.asp')




#%%

for n in tqdm(REGISTROS.index[:]):
    
    
    try:   
       
        WebDriverWait(navegador, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="txtCPF"]'))).click()
        WebDriverWait(navegador, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="txtCPF"]'))).clear()       
        WebDriverWait(navegador, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="txtCPF"]'))).send_keys(re.sub('[.-]', '', REGISTROS['CPF'][n]))
        
        WebDriverWait(navegador, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="txtDataNascimento"]'))).clear()
        WebDriverWait(navegador, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="txtDataNascimento"]'))).send_keys(REGISTROS['NASCIMENTO'][n])
        
        
        # chavesite=navegador.find_element(By.ID,'hcaptcha').get_attribute('data-sitekey')        
        # quebracaptcha(chavesite)
        
        # Espera até que o frame esteja presente e então muda o contexto para o frame
        WebDriverWait(navegador, 10).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//*[@id="hcaptcha"]/iframe')))

        # Localiza a checkbox e clica nela
        checkbox = WebDriverWait(navegador, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="checkbox"]')))
        checkbox.click()
        time.sleep(5)
        navegador.switch_to.default_content()

        
        WebDriverWait(navegador, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="id_submit"]'))).click()
       
        # WebDriverWait(navegador, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[2]/div[1]/div/div/div/div/div/div[1]/div[2]/p/span[4]/b')))
        
        try:
            situacao = navegador.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[1]/div/div/div/div/div/div[1]/div[2]/p/span[4]/b').text
         
            if situacao=='TITULAR FALECIDO':
                
                anoobito = navegador.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[1]/div/div/div/div/div/div[1]/div[3]/p[2]/span[1]/b[2]').text
                # navegador.execute_script('window.print();')
                # time.sleep(5)
                # default_filepath = os.path.join(download_dir, default_filename)
                # new_filename = re.sub('[.-]', '', REGISTROS['CPF'][n])+'.pdf'
                # new_filepath = os.path.join(download_dir, new_filename)

                # # Renomeia o arquivo PDF
                # if os.path.exists(default_filepath):
                #     os.rename(default_filepath, new_filepath)
                
            else:
                anoobito=''
        except:
            teste=navegador.find_element(By.XPATH, '//*[@id="content-core"]/div/div/div[1]/span/h4/b').text
            
            if 'divergente' in teste:
                situacao='DADOS DIVERGENTES'
                anoobito=''
                
        config = {  'user': 'root',
                  'password': senhamysql,
                  'host': 'localhost',
                  'database': 'cobranca',
                  }
        columns = ['CPF', 'NOME', 'NASCIMENTO','REGIONAL','SITUACAO', 'ANOOBITO']  
        values = [REGISTROS['CPF'][n], REGISTROS['NOME'][n],REGISTROS['NASCIMENTO'][n],REGISTROS['REGIONAL'][n], situacao, anoobito] 
        values[1] = values[1].replace("'", "")

        columns_str = ', '.join(columns)
        values_str = ', '.join([f"'{value}'" if isinstance(value, str) else str(value) for value in values])              
                          
    
        connection = mysql.connect(**config)
        cursor = connection.cursor()
                                
             # Criar a query de inserção com acentos graves nas colunas
            
        query = f"INSERT INTO situacaocpf ({columns_str}) VALUES ({values_str})"
                                
                                                                   
            # Executar a query
        cursor.execute(query)
                                
            # Commit para aplicar as alterações
        connection.commit()
        
        WebDriverWait(navegador, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="idRodape"]/p[4]/a/span'))).click()
        # time.sleep(10)
        
    except Exception as e:
        try:
            WebDriverWait(navegador, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="idRodape"]/p[4]/a/span'))).click()
            continue
        except:
            navegador.refresh()
            pass
navegador.quit()
 
#%%

