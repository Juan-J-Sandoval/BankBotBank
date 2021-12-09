import os
import json
import boto3
from datetime import datetime

rds_data = boto3.client('rds-data')

# configuracion de auroraserveless
cluster_arn = os.environ['cluster_arn_aurora']
secret_arn = os.environ['secret_arn_aurora']

def lambda_handler(event, context):
    print(event)
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
        
    return result

def createItem(item, diccionary):
    now = datetime.now()
    sql = """
    INSERT INTO Conversations( sessionId, userMessage, lastState, intent, lastQuestion, botMessage, startConversation, endConversation, updated, created)
    VALUES(:sessionId, :userMessage, :lastState, :intent, :lastQuestion, :botMessage, :startConversation, :endConversation, :updated, :created)
    """
    sessionId = {'name': 'sessionId', 'value': {'stringValue': item['sessionId']}}
    userMessage = {'name': 'userMessage', 'value': {'stringValue': item['userMessage']}}
    lastState = {'name': 'lastState', 'value': {'stringValue': item['lastState']}}
    intent = {'name': 'intent', 'value': {'stringValue': 'init'}}
    lastQuestion={'name': 'lastQuestion', 'value':{'longValue': 0}}
    botMessage = {'name': 'botMessage', 'value': {'stringValue': item['botMessage']}}
    startConversation = {'name':'startConversation', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
    endConversation = {'name':'endConversation', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
    updated = {'name':'updated', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
    created = {'name':'created', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
    parameters = [sessionId, userMessage, lastState, intent, lastQuestion, botMessage, startConversation, endConversation, updated, created]
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
    else:
        result = {
            'code': 400,
            'message': "No puede crear la conversacion"
        }
    return result


def getItem(item, diccionary):
    if 'sessionId' not in diccionary  :
        result = {
            'code': 400,
            'message': "Error parametros requeridos"
        }
    else :
        sql = """ 
            SELECT * from Conversations WHERE sessionId = :sessionId
            """
        sessionId = {'name': 'sessionId', 'value': {'stringValue': item['sessionId']}}
            
        response = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [sessionId])

        payload_item = json.loads(json.dumps(response))
        rows = []
        rows = responseQuery(payload_item)
        
        if 'records' not in payload_item:
            result = {
                'code': 400,
                'message': "No se encuentra el sessionId enviando"
            }
        else:
            rows
            result = {
                'code': 200,
                'message': rows
            }

    return result


def updateItem(item, diccionary):
    now = datetime.now()
    if 'sessionId' not in diccionary  :
        result = {
            'code': 400,
            'message': "No puede encontrar la conversacion, faltan datos requeridos"
        }
    else:
        sql = """ 
        SELECT * from Conversations WHERE sessionId = :sessionId
        """
        sessionId = {'name': 'sessionId', 'value': {'stringValue': item['sessionId']}}
            
        response = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [sessionId])
            
        payload_item = json.loads(json.dumps(response))

        if 'records' not in payload_item:
            result = {
                'code': 400,
                'message': "Conversacion no registrada"
            }
        else:
            sql = """
            UPDATE Conversations set userMessage =:userMessage, lastState=:lastState, intent = :intent, 
            lastQuestion = :lastQuestion, botMessage = :botMessage, endConversation = :endConversation,
            updated = :updated WHERE sessionId = :sessionId
            """
            sessionId = {'name': 'sessionId', 'value': {'stringValue': item['sessionId']}}
            userMessage = {'name': 'userMessage', 'value': {'stringValue': item['userMessage']}}
            lastState = {'name': 'lastState', 'value': {'stringValue': item['lastState']}}
            intent = {'name': 'intent', 'value': {'stringValue': item['intent']}}
            lastQuestion={'name': 'lastQuestion', 'value':{'longValue': item['lastQuestion']}}
            botMessage = {'name': 'botMessage', 'value': {'stringValue': item['botMessage']}}
            endConversation = {'name':'endConversation', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
            updated = {'name':'updated', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
            parameters = [sessionId, userMessage, lastState, intent, lastQuestion, botMessage, endConversation, updated]

            response = rds_data.execute_statement(
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = parameters)

            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                result = {
                    'code': 200,
                    'message': "Conversacion actualizado correctamente"
                }
            else :
                result = {
                    'code': 400,
                    'message': "No puede actualizar la conversacion"
                }
    return result     


def deleteItem(item, diccionary):
    now = datetime.now()
    if 'sessionId' not in diccionary  :
        result = {
            'code': 400,
            'message': "No puede encontrar la conversacion, faltan datos requeridos"
        }
    else :
        sql = """ 
        SELECT * from Conversations WHERE sessionId = :sessionId
        """
        sessionId = {'name': 'sessionId', 'value': {'stringValue': item['sessionId']}}
            
        response = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [sessionId])
            
        payload_item = json.loads(json.dumps(response))

        if 'records' not in payload_item:
            result = {
                'code': 400,
                'message': "Conversacion no registrada"
            }
        else :
            
            sql = """
            DELETE FROM Conversations WHERE sessionId = :sessionId
            """
            sessionId = {'name': 'sessionId', 'value': {'stringValue': item['sessionId']}}
            parameters = [sessionId]
            response = rds_data.execute_statement(
                resourceArn = cluster_arn, 
                secretArn = secret_arn, 
                database = os.environ['name_db'], 
                sql = sql,
                parameters = parameters)

            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                result = {
                    'code': 200,
                    'message': "Conversacion eliminada correctamente"
                }
            else :
                result = {
                    'code': 400,
                    'message': "No puede eliminar la conversacion"
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
                row[cols[i]] = None
            i += 1

        rows.append(row)
    return rows