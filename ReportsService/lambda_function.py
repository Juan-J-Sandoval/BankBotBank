import os
import json
import boto3
import hashlib
from datetime import datetime

rds_data = boto3.client('rds-data')


# configuracion de auroraserveless
cluster_arn = os.environ['cluster_arn_aurora']
secret_arn = os.environ['secret_arn_aurora']


def lambda_handler(event, context):
    
    payload_dictionary = json.loads(json.dumps(event['payload']['Item']))
    
    operation = event['operation']
    
    if operation == 'create':
        result = createItem(event['payload']['Item'], payload_dictionary)
    
    elif operation=='fullGet':
        result = fullGet()

    elif operation=='getReportByDate':
        result = getReportByDate(event['payload']['Item'], payload_dictionary)
    
    elif operation=='getReportByStatus':
        result = getReportByStatus(event['payload']['Item'], payload_dictionary)

    elif operation=='getReportByAgent':
        result = getReportByAgent(event['payload']['Item'], payload_dictionary)

    elif operation=='update':
        result = updateItem(event['payload']['Item'], payload_dictionary)
    
    elif operation=='delete':
        result = deleteItem(event['payload']['Item'], payload_dictionary)
    
    return result
    

def createItem(item, diccionary):
    reportId = hashlib.shake_128(item['comment'].encode()).hexdigest(5)
    if 'agent' not in diccionary or 'comment' not in diccionary or 'priorityAttention' not in diccionary or 'processStatus' not in diccionary:
        result = {
            'code': 400,
            'message': "No puede crear el reporte, faltan datos requeridos"
        }
    else :

        sql = """ 
            SELECT * from Reports WHERE reportId = :reportId
            """
        parameters = {'name': 'reportId', 'value': {'stringValue': reportId}}
            
        response = rds_data.execute_statement(
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [parameters])
        
        if len(response['records']) > 0:
            result = {
                'code': 400,
                'message': "Correo ya registrado"
            }
        else :
            now = datetime.now()
            sql = """
            INSERT INTO Reports( reportId, agent, comment, priorityAttention, processStatus, updated, created)
            VALUES(:reportId, :agent, :comment, :priorityAttention, :processStatus, :updated, :created)
            """
            reportId = {'name': 'reportId', 'value': {'stringValue': reportId}}
            agent = {'name': 'agent', 'value': {'stringValue': item['agent']}}
            comment = {'name': 'comment', 'value': {'stringValue': item['comment']}}
            priorityAttention = {'name': 'priorityAttention', 'value': {'booleanValue': item['priorityAttention']}}
            processStatus = {'name': 'processStatus', 'value': {'stringValue': item['processStatus']}}
            updated = {'name':'updated', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
            created = {'name':'created', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
            parameters = [reportId, agent, comment, priorityAttention, processStatus, updated, created]
 
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


def fullGet():
    sql = """ 
        SELECT * from Reports
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
            'message': "No se encuentra el email enviando"
        }
    else:
        result = {
            'code': 200,
            'message': rows
        }
    return result
    
def getReportByDate(item, diccionary):
    if 'dateStart' not in diccionary or 'dateEnd' not in diccionary:
        result = {
            'code': 400,
            'message': "No consulta reportes, faltan datos requeridos"
        }
    else :
        sql = """ 
            SELECT * from Reports WHERE created >= :dateStart AND created <= :dateEnd
            """
        dateStart = {'name':'dateStart', 'value':{'stringValue': item['dateStart']}}
        dateEnd = {'name':'dateEnd', 'value':{'stringValue': item['dateEnd']}}
        response = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [dateStart, dateEnd])
        rows = []
        rows = responseQuery(response)
    if 'records' not in response:
        result = {
            'code': 400,
            'message': "No se encuentran reportes"
        }
    else:
        result = {
            'code': 200,
            'message': rows
        }
    return result

def getReportByStatus(item, diccionary):
    if 'status' not in diccionary:
        result = {
            'code': 400,
            'message': "No consulta reportes, faltan datos requeridos"
        }
    else :
        sql = """ 
            SELECT * from Reports WHERE processStatus = :status 
            """
        status = {'name':'status', 'value':{'stringValue': item['status']}}
        response = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [status])
        rows = []
        rows = responseQuery(response)
    if 'records' not in response:
        result = {
            'code': 400,
            'message': "No se encuentran reportes"
        }
    else:
        result = {
            'code': 200,
            'message': rows
        }
    return result

def getReportByAgent(item, diccionary):
    if 'agent' not in diccionary:
        result = {
            'code': 400,
            'message': "No consulta reportes, faltan datos requeridos"
        }
    else :
        sql = """ 
            SELECT * from Reports WHERE agent = :agent 
            """
        agent = {'name':'agent', 'value':{'stringValue': item['agent']}}
        response = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [agent])
        rows = []
        rows = responseQuery(response)
    if 'records' not in response:
        result = {
            'code': 400,
            'message': "No se encuentran reportes"
        }
    else:
        result = {
            'code': 200,
            'message': rows
        }
    return result

def updateItem(item, diccionary):
    if 'reportId' not in diccionary  :
        result = {
            'code': 400,
            'message': "No puede buscar el reporte, faltan datos requeridos"
        }
    else :
        sql = """ 
            SELECT * from Reports WHERE reportId = :reportId
            """
        reportId = {'name': 'reportId', 'value': {'stringValue': item['reportId']}}
            
        response = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [reportId])

        payload_item = json.loads(json.dumps(response))
        
        if 'records' not in payload_item:
            result = {
                'code': 400,
                'message': "Reporte no registrado"
            }
        else :
            now = datetime.now()
            sql = """
            UPDATE Reports SET agent = :agent, comment = :comment, priorityAttention = :priorityAttention, 
                processStatus = :processStatus, updated = :updated
            WHERE reportId = :reportId
            """
            reportId = {'name': 'reportId', 'value': {'stringValue': item['reportId']}}
            agent = {'name': 'agent', 'value': {'stringValue': item['agent']}}
            comment = {'name': 'comment', 'value': {'stringValue': item['comment']}}
            priorityAttention = {'name': 'priorityAttention', 'value': {'booleanValue': item['priorityAttention']}}
            processStatus = {'name': 'processStatus', 'value': {'stringValue': item['processStatus']}}
            updated = {'name':'updated', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
            parameters = [reportId, agent, comment, priorityAttention, processStatus, updated]
 
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
                    'message': "No puede actualizar el reporte"
                }
    
    return result     
    
def deleteItem(item, diccionary):
    if 'reportId' not in diccionary  :
        result = {
            'code': 400,
            'message': "No puede buscar al usuario, faltan datos requeridos"
        }
    else :
        sql = """ 
            SELECT * from Reports WHERE reportId = :reportId
            """
        reportId = {'name': 'reportId', 'value': {'stringValue': item['reportId']}}
            
        response = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [reportId])

        payload_item = json.loads(json.dumps(response))
        
        if 'records' not in payload_item:
            result = {
                'code': 400,
                'message': "Reporte no registrado"
            }
        else :
            
            sql = """ 
            DELETE FROM Reports WHERE reportId = :reportId
            """
            reportId = {'name': 'reportId', 'value': {'stringValue': item['reportId']}}
                
            response = rds_data.execute_statement(
                includeResultMetadata = True,
                resourceArn = cluster_arn, 
                secretArn = secret_arn, 
                database = os.environ['name_db'], 
                sql = sql,
                parameters = [reportId])
    
            payload_item = json.loads(json.dumps(response))
            
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                result = {
                    'code': 200,
                    'message': "Registro eliminado correctamente"
                }
            else :
                result = {
                    'code': 400,
                    'message': "No puede eliminar el reporte"
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