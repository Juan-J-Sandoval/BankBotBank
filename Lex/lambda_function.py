import json, boto3, os, time
s3 = boto3.client('s3')
lex = boto3.client('lex-models')
def lambda_handler(event, context):
    print('>>> ',event)
    #Extrae el zip del bucket 
    s3Response = s3.get_object(Bucket=event['bucket'],Key=event['zip'])
    dataB = s3Response['Body'].read()
    #Se importa el zip a lex. Esto no lo construira, solo verifica que el zip lleve los archivos correctos
    lexImport = lex.start_import(
        payload=dataB,
        resourceType='BOT',
        mergeStrategy='OVERWRITE_LATEST'
    )
    #Se verifica que el estado de importación sea diferente a IN_PROGRESS
    lexGetImport = lex.get_import(importId=lexImport['importId'])
    while lexGetImport['importStatus'] == 'IN_PROGRESS':
        time.sleep(15)
        lexGetImport = lex.get_import(importId=lexImport['importId'])
    #Se extraen las versiones del bot previamente importado, para despues extraer los datos de la version $LATEST junto con su Checksum
    lexBotVersion= lex.get_bot_versions(name=lexImport['name'])
    lexBot = lex.get_bot(name=lexBotVersion['bots'][0]['name'], versionOrAlias=lexBotVersion['bots'][0]['version'])
    #Se reenvían los datos pero ahora se especifica el 'processBehavior' en BUILD para que el estado final del bot sea BUILDING
    lexPutBot= lex.put_bot(
        name=lexBot['name'],
        locale=lexBot['locale'],
        childDirected=lexBot['childDirected'],
        checksum=lexBot['checksum'],
        abortStatement = lexBot['abortStatement'],
        intents= lexBot['intents'],
        processBehavior='BUILD'
    )
    #Si se desea verificar que el bot está funcionando, se debe agregar un time sleep y volver a consultar con get_bot hasta que el estado sea READY
    return {"NameBot":lexPutBot['name'], "Status":lexPutBot['status'], "Checksum":lexPutBot['checksum'], "Version":lexPutBot['version']}
