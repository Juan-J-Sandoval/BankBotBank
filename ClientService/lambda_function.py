import os
import json
import boto3
import hashlib 
import uuid
from datetime import datetime, timezone

rds_data = boto3.client('rds-data')

# configuracion de auroraserveless
cluster_arn = os.environ['cluster_arn_aurora']
secret_arn = os.environ['secret_arn_aurora']

def lambda_handler(event, context):
    
    print("Received event: " + json.dumps(event, indent=2))
    print("evento " + event['operation'])
    
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
    
    elif operation=='checkemail':
        result = checkemail(event['payload']['Item'], payload_dictionary)

        
    return result
    
def createItem(item, diccionary):

    if 'email' not in diccionary or 'name' not in diccionary or 'lastName' not in diccionary or 'phone' not in diccionary or 'password' not in diccionary :
        result = {
            'code': 400,
            'message': "No puede crear el cliente, faltan datos requeridos"
        }
    else :
        item['password'] = hashlib.md5(item['password'].encode()).hexdigest()

        sql = """ 
            SELECT * from Clients WHERE email = :email
            """
        email = {'name': 'email', 'value': {'stringValue': item['email']}}
            
        response = rds_data.execute_statement(
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [email])
        
        if len(response['records']) > 0:
            result = {
                'code': 400,
                'message': "Correo ya registrado"
            }
        else :
            now = datetime.now()
            sql = """
            INSERT INTO Clients( email, name, lastName, phone, updated, created)
            VALUES(:email, :name, :lastname, :phone, :updated, :created)
            """
            name = {'name': 'name', 'value': {'stringValue': item['name']}}
            lastName = {'name': 'lastname', 'value': {'stringValue': item['lastName']}}
            phone = {'name': 'phone', 'value': {'stringValue': item['phone']}}
            updated = {'name':'updated', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
            created = {'name':'created', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
            parameters = [email, name, lastName, phone, updated, created]
 
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
                    'message': "No puede crear el cliente"
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
            SELECT * from Clients WHERE email = :email
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
    
def checkemail( item, diccionary):
    if 'email' not in diccionary or 'password' not in diccionary :
        result = {
            'code': 400,
            'message': "No puede buscar al cliente, faltan datos requeridos"
        }
    else :
        item['password'] = hashlib.md5(item['password'].encode()).hexdigest()
        sql = """ 
            SELECT * from Clients WHERE email = :email and password = :password
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
            'message': "No puede buscar al cliente, faltan datos requeridos"
        }
    else :
        sql = """ 
            SELECT * from Clients WHERE email = :email
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
                'message': "Cliente no registrado"
            }
        else :
            
            item['password'] = hashlib.md5(item['password'].encode()).hexdigest()
        
            now = datetime.now()
            sql = """
            UPDATE Clients SET email = :email, name = :name, lastName = :lastname, 
                phone = :phone, updated = :updated
            WHERE id = :id
            """
            name = {'name': 'name', 'value': {'stringValue': item['name']}}
            lastName = {'name': 'lastname', 'value': {'stringValue': item['lastName']}}
            phone = {'name': 'phone', 'value': {'stringValue': item['phone']}}
            updated = {'name':'updated', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
            id_ = {'name': 'id', 'value': {'longValue': item['id']}}
            parameters = [email, name, lastName, phone, updated, id_]
 
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
                    'message': "No puede crear el cliente"
                }
    
    return result     
    
def deleteItem(item, diccionary):
    if 'id' not in diccionary  :
        result = {
            'code': 400,
            'message': "No puede buscar al cliente, faltan datos requeridos"
        }
    else :
        sql = """ 
            SELECT * from Clients WHERE email = :email
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
                'message': "Cliente no registrado"
            }
        else :
            
            sql = """ 
            DELETE FROM Clients WHERE email = :email
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
                    'message': "No puede eliminar el cliente"
                }
    
    return result         

def responseQuery(payload_item):
    
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
                row[cols[i]] = null
            i += 1

        rows.append(row)
        
    return rows