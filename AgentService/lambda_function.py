import os
import json
import boto3
import hashlib 
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from random import choice
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

rds_data = boto3.client('rds-data')

valores = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ<=>@#%&+"

# configuracion de auroraserveless
cluster_arn = os.environ['cluster_arn_aurora']
secret_arn = os.environ['secret_arn_aurora']


def lambda_handler(event, context):
    
    payload_dictionary = json.loads(json.dumps(event['payload']['Item']))
    
    operation = event['operation']
    
    if operation == 'create':
        result = createItem(event['payload']['Item'], payload_dictionary)

    elif operation=='get':
        result = getItem(event['payload']['Item'], payload_dictionary)
            
    elif operation=='update':
        result = updateItem(event['payload']['Item'], payload_dictionary)
    
    elif operation=='delete':
        result = deleteItem(event['payload']['Item'], payload_dictionary)
    
    elif operation=='login':
        result = login(event['payload']['Item'], payload_dictionary)

    elif operation=='recoverPasswd':
        result = recoverPasswd(event['payload']['Item'], payload_dictionary)
    
    elif operation=='fullGet':
        result = fullGet()
    
    elif operation=='getUsersByRol':
        result = getUsersByRol(event['payload']['Item'], payload_dictionary)

    elif operation=='getByNameLast':
        result = getByNameLast(event['payload']['Item'], payload_dictionary)

    elif operation=='getUsersByState':
        result = getUsersByState(event['payload']['Item'], payload_dictionary)

    return result
    

def createItem(item, diccionary):

    if 'email' not in diccionary or 'name' not in diccionary or 'lastName' not in diccionary or 'phone' not in diccionary or 'password' not in diccionary :
        result = {
            'code': 400,
            'message': "No puede crear el usuario, faltan datos requeridos"
        }
    else :
        item['password'] = hashlib.md5(item['password'].encode()).hexdigest()

        sql = """ 
            SELECT * from Agents WHERE email = :email
            """
        email = {'name': 'email', 'value': {'stringValue': item['email']}}
            
        response = rds_data.execute_statement(
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [email])

        print("response", response)
        
        if len(response['records']) > 0:
            result = {
                'code': 400,
                'message': "Correo ya registrado"
            }
        else :
            now = datetime.now()
            sql = """
            INSERT INTO Agents( email, name, lastName, phone, password, rol, lastState, position, updated, created,
            Dashboard, Chat, Reportes, Respuestas, MiCuenta, RecuperarPsswrd, Consultar, Nuevo, sessionId)
            VALUES(:email, :name, :lastname, :phone, :password, :rol, :lastState, :position, :updated, :created,
            :Dashboard, :Chat, :Reportes, :Respuestas, :MiCuenta, :RecuperarPsswrd, :Consultar, :Nuevo, :sessionId)
            """
            name = {'name': 'name', 'value': {'stringValue': item['name']}}
            lastName = {'name': 'lastname', 'value': {'stringValue': item['lastName']}}
            password = {'name': 'password', 'value': {'stringValue': item['password']}}
            phone = {'name': 'phone', 'value': {'stringValue': item['phone']}}
            lastState = {'name': 'lastState', 'value': {'stringValue': item['lastState']}}
            position = {'name': 'position', 'value': {'stringValue': item['position']}}
            updated = {'name':'updated', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
            created = {'name':'created', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
            rol = {'name': 'rol', 'value': {'stringValue': item['rol']}}
            Dashboard = {'name': 'Dashboard', 'value': {'booleanValue': item['Dashboard']}}
            Chat = {'name': 'Chat', 'value': {'booleanValue': item['Chat']}}
            Reportes = {'name': 'Reportes', 'value': {'booleanValue': item['Reportes']}}
            Respuestas = {'name': 'Respuestas', 'value': {'booleanValue': item['Respuestas']}}
            MiCuenta = {'name':'MiCuenta', 'value':{'booleanValue': item['MiCuenta']}}
            RecuperarPsswrd = {'name':'RecuperarPsswrd', 'value':{'booleanValue': item['RecuperarPsswrd']}}
            Consultar = {'name':'Consultar', 'value':{'booleanValue': item['Consultar']}}
            Nuevo = {'name':'Nuevo', 'value':{'booleanValue': item['Nuevo']}}
            sessionId = {'name': 'sessionId', 'value': {'stringValue': item['sessionId']}}
            parameters = [email, name, lastName, phone, password, rol, lastState, position, updated, created,
                Dashboard, Chat, Reportes, Respuestas, MiCuenta, RecuperarPsswrd, Consultar, Nuevo, sessionId
            ]
 
            response = rds_data.execute_statement(
                resourceArn = cluster_arn, 
                secretArn = secret_arn, 
                database = os.environ['name_db'], 
                sql = sql,
                parameters = parameters)

            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                result = {
                    'code': 200,
                    'message': "Registrado correctamente"
                }
            else :
                result = {
                    'code': 400,
                    'message': "No puede crear el usuario"
                }
    
    return result

def getItem(item, diccionary):
    if 'email' not in diccionary  :
        result = {
            'code': 400,
            'message': "Error parametros requeridos"
        }
    else :
        sql = """ 
            SELECT * from Agents WHERE email = :email
            """
        email = {'name': 'email', 'value': {'stringValue': item['email']}}
            
        response = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [email])

        payload_item = json.loads(json.dumps(response))
        rows = []
        rows = responseQuery(payload_item)
        
        if 'records' not in payload_item:
            result = {
                'code': 400,
                'message': "No se encuentra el email enviando"
            }
        else:
            rows
            result = {
                'code': 200,
                'message': rows
            }

    return result
    
def login(item, diccionary):
    if 'email' not in diccionary or 'password' not in diccionary :
        result = {
            'code': 400,
            'message': "No puede buscar al usuario, faltan datos requeridos"
        }
    else :
        item['password'] = hashlib.md5(item['password'].encode()).hexdigest()
        sql = """ 
            SELECT * from Agents WHERE email = :email and password = :password
            """
        email = {'name': 'email', 'value': {'stringValue': item['email']}}
        password = {'name': 'password', 'value': {'stringValue': item['password']}}
        response = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [email, password])

        payload_item = json.loads(json.dumps(response))
        rows = []
        rows = responseQuery(payload_item)

        if 'records' not in payload_item:
            result = {
                'code': 400,
                'message': "Usuario no registrado"
            }
        else :
            result = {
                'code': 200,
                'message': rows
            }
            
    return result

def updateItem(item, diccionary):
    if 'id' not in diccionary  :
        result = {
            'code': 400,
            'message': "No puede buscar al usuario, faltan datos requeridos"
        }
    else :
        sql = """ 
            SELECT * from Agents WHERE email = :email
            """
        email = {'name': 'email', 'value': {'stringValue': item['email']}}
            
        response = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [email])

        payload_item = json.loads(json.dumps(response))
        
        if 'records' not in payload_item:
            result = {
                'code': 400,
                'message': "Usuario no registrado"
            }
        else :
            
            #item['password'] = hashlib.md5(item['password'].encode()).hexdigest()
        
            now = datetime.now()
            sql = """
            UPDATE Agents SET email = :email, name = :name, lastName = :lastname, 
                phone = :phone, password = :password, rol = :rol,
                lastState = :lastState, position = :position, updated = :updated,
                Dashboard = :Dashboard, Chat = :Chat, Reportes = :Reportes,
                Respuestas = :Respuestas, MiCuenta = :MiCuenta, RecuperarPsswrd = :RecuperarPsswrd,
                Consultar = :Consultar, Nuevo = :Nuevo
            WHERE id = :id
            """
            name = {'name': 'name', 'value': {'stringValue': item['name']}}
            lastName = {'name': 'lastname', 'value': {'stringValue': item['lastName']}}
            password = {'name': 'password', 'value': {'stringValue': item['password']}}
            phone = {'name': 'phone', 'value': {'stringValue': item['phone']}}
            rol = {'name': 'rol', 'value': {'stringValue': item['rol']}}
            lastState = {'name': 'lastState', 'value': {'stringValue': item['lastState']}}
            position = {'name': 'position', 'value': {'stringValue': item['position']}}
            updated = {'name':'updated', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
            id_ = {'name': 'id', 'value': {'longValue': item['id']}}
            Dashboard = {'name': 'Dashboard', 'value': {'booleanValue': item['Dashboard']}}
            Chat = {'name': 'Chat', 'value': {'booleanValue': item['Chat']}}
            Reportes = {'name': 'Reportes', 'value': {'booleanValue': item['Reportes']}}
            Respuestas = {'name': 'Respuestas', 'value': {'booleanValue': item['Respuestas']}}
            MiCuenta = {'name':'MiCuenta', 'value':{'booleanValue': item['MiCuenta']}}
            RecuperarPsswrd = {'name':'RecuperarPsswrd', 'value':{'booleanValue': item['RecuperarPsswrd']}}
            Consultar = {'name':'Consultar', 'value':{'booleanValue': item['Consultar']}}
            Nuevo = {'name':'Nuevo', 'value':{'booleanValue': item['Nuevo']}}
            parameters = [email, name, lastName, phone, password, rol, lastState, position, updated, id_,
                Dashboard, Chat, Reportes, Respuestas, MiCuenta, RecuperarPsswrd, Consultar, Nuevo
            ]
 
            response = rds_data.execute_statement(
                resourceArn = cluster_arn, 
                secretArn = secret_arn, 
                database = os.environ['name_db'], 
                sql = sql,
                parameters = parameters)
        
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                result = {
                    'code': 200,
                    'message': "Registro actualizado correctamente"
                }
            else :
                result = {
                    'code': 400,
                    'message': "No puede crear el usuario"
                }
    
    return result     

def deleteItem(item, diccionary):
    if 'id' not in diccionary  :
        result = {
            'code': 400,
            'message': "No puede buscar al usuario, faltan datos requeridos"
        }
    else :
        sql = """ 
            SELECT * from Agents WHERE email = :email
            """
        email = {'name': 'email', 'value': {'stringValue': item['email']}}
            
        response = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [email])

        payload_item = json.loads(json.dumps(response))
        
        if 'records' not in payload_item:
            result = {
                'code': 400,
                'message': "Usuario no registrado"
            }
        else :
            
            sql = """ 
            DELETE FROM Agents WHERE email = :email
            """
            email = {'name': 'email', 'value': {'stringValue': item['email']}}
                
            response = rds_data.execute_statement(
                includeResultMetadata = True,
                resourceArn = cluster_arn, 
                secretArn = secret_arn, 
                database = os.environ['name_db'], 
                sql = sql,
                parameters = [email])
    
            payload_item = json.loads(json.dumps(response))
            
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                result = {
                    'code': 200,
                    'message': "Registro eliminado correctamente"
                }
            else :
                result = {
                    'code': 400,
                    'message': "No puede eliminar el usuario"
                }
    
    return result

def recoverPasswd(item, diccionary):
    if 'email' not in diccionary:
        result = {
            'code': 400,
            'message': "No puede buscar al usuario, faltan datos requeridos"
        }
    else :
        p = ""
        p = p.join([choice(valores) for i in range(10)])
        message = "Tu nueva contraseña es: "+p
        p= hashlib.md5(p.encode()).hexdigest()
        print(p)
        
        now = datetime.now()
        sql = """
        UPDATE Agents SET password = :password, updated = :updated
        WHERE email = :email
        """
        password = {'name': 'password', 'value': {'stringValue': p}}
        updated = {'name':'updated', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
        email = {'name': 'email', 'value': {'stringValue':item['email']}}
        parameters = [email, password, updated]

        response = rds_data.execute_statement(
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = parameters)
            
        if response['numberOfRecordsUpdated'] == 1:

            SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            service = build('gmail', 'v1', credentials=creds)
            mimeMessage = MIMEMultipart()
            mimeMessage["to"] = item['email']
            mimeMessage["subject"] = "Nueva contraseña"
            mimeMessage.attach(MIMEText(message, "plain"))
            raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()
            message = service.users().messages().send(userId = "me", body = {"raw": raw_string}).execute()
            print("api gmail > ",message)

            result = {
                'code': 200,
                'message': "Registro actualizado correctamente"
            }
        else :
            result = {
                'code': 400,
                'message': "No puede actualizar contraseña"
            }
    return result

def fullGet():
    sql = """ 
        SELECT * from Agents
        """
        
    response = rds_data.execute_statement(
        includeResultMetadata = True,
        resourceArn = cluster_arn, 
        secretArn = secret_arn, 
        database = os.environ['name_db'], 
        sql = sql
    )

    payload_item = json.loads(json.dumps(response))
    rows = []
    rows = responseQuery(payload_item)
    
    if 'records' not in payload_item:
        result = {
            'code': 400,
            'message': "No se encuentran usuarios"
        }
    else:
        result = {
            'code': 200,
            'message': rows
        }
    return result

def getUsersByRol(item, diccionary):
    if 'rol' not in diccionary:
        result = {
            'code': 400,
            'message': "No consulta usuarios, faltan datos requeridos"
        }
    else :
        sql = """ 
            SELECT * from Agents WHERE rol = :rol 
            """
        rol = {'name':'rol', 'value':{'stringValue': item['rol']}}
        response = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [rol])
        rows = []
        rows = responseQuery(response)
    if 'records' not in response:
        result = {
            'code': 400,
            'message': "No se encuentran usuarios"
        }
    else:
        result = {
            'code': 200,
            'message': rows
        }
    return result

def getByNameLast(item, diccionary):
    if 'name' not in diccionary and 'lastName' not in diccionary:
        result = {
            'code': 400,
            'message': "No consulta usuarios, faltan datos requeridos"
        }
    else:
        sql = """ 
            SELECT * from Agents WHERE name = :name and lastName = :lastName
            """
        name = {'name':'name', 'value':{'stringValue': item['name']}}
        lastName = {'name':'lastName', 'value':{'stringValue': item['lastName']}}
        response = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [name, lastName])
        rows = []
        rows = responseQuery(response)
        if 'records' not in response:
            result = {
                'code': 400,
                'message': "No se encuentran usuarios"
            }
        else:
            result = {
                'code': 200,
                'message': rows
            }
    return result

def getUsersByState(item, diccionary):
    if 'lastState' not in diccionary:
        result = {
            'code': 400,
            'message': "No consulta usuarios, faltan datos requeridos"
        }
    else :
        sql = """ 
            SELECT * from Agents WHERE lastState = :lastState 
            """
        lastState = {'name':'lastState', 'value':{'stringValue': item['lastState']}}
        response = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [lastState])
        rows = []
        rows = responseQuery(response)
    if 'records' not in response:
        result = {
            'code': 400,
            'message': "No se encuentran usuarios"
        }
    else:
        result = {
            'code': 200,
            'message': rows
        }
    return result

def responseQuery(payload_item):
    print(json.dumps(payload_item))
    rows = []
    cols = []
    for column in payload_item['columnMetadata']:
        cols.append(column['name'])
    for record in payload_item['records'] :
        i = 0
        row = {}
        for item in record:
            print (item, i)
            if 'stringValue' in item  :
                row[cols[i]] = item['stringValue']
            elif 'blobValue' in item :
                row[cols[i]] = item['blobValue']
            elif 'doubleValue' in item :
                row[cols[i]] = item['doubleValue']
            elif 'longValue' in item :
                row[cols[i]] = item['longValue']
            elif 'booleanValue' in item:
                row[cols[i]] = item['booleanValue']
            else :
                row[cols[i]] = None
            i += 1

        rows.append(row)
        
    return rows