import json, boto3, os, re
lambdas = boto3.client('lambda')
lambdaSnips = os.environ['Snips']
bucket_name = os.environ['BUCKET_NAME']
bot_data_file = os.environ['BOT_DATA_FILE']
s3 = boto3.client('s3')
s3.download_file(bucket_name,bot_data_file,"/tmp/"+bot_data_file)
f = open("/tmp/"+bot_data_file, "r")
content = f.read()
dataBot = json.loads(content)

def lambda_handler(event, context):
    print(">>> ",event)
    estado = event['estado']; n_pregunta = event["n_pregunta"]
    if event["n_pregunta"] == 5:
        respuesta = "Gracias por ingresar tus datos, un agente se contactara con usted en menos de 24 horas"
        n_pregunta = 0
        estado = "cm"
    elif n_pregunta == 0:
        entidades = {"toggledEntities":{"SYS.NOMBRE":"True"}}
        respSnips = entidadesSnips(event['mensaje'], entidades)
        if respSnips['intent'] == "aceptar":
            respuesta =dataBot["ResponseVenta"][n_pregunta]
            n_pregunta  += 1
        else:
            respuesta = "Cancelaste el registro de tus datos, NO se te podrá contactar"
            estado = "cm"
    elif n_pregunta == 1:
        entidades = {"toggledEntities":{"SYS.NOMBRE":"True"}}
        respSnips = entidadesSnips(event['mensaje'], entidades)
        if respSnips['entity'] == "SYS.NOMBRE":
            respuesta =dataBot["ResponseVenta"][n_pregunta]
            n_pregunta  += 1
        else:
            respuesta = "Ingresa tu nombre y apellido para continuar con el proceso, recuerda ingresar datos reales. Si tienes otra duda reinicia el chat."
    elif n_pregunta == 2:
        entidades = {"toggledEntities":{"SYS.TELEFONO":"True"}}
        respSnips = entidadesSnips(event['mensaje'], entidades)
        if respSnips['entity'] == "SYS.TELEFONO":
            respuesta =dataBot["ResponseVenta"][n_pregunta]
            n_pregunta  += 1
        else:
            respuesta = "Ingresa un número telefónico a solo 10 digitos, recuerda ingresar datos reales. Si tienes otra duda reinicia el chat."
    elif n_pregunta == 3:
        entidades = {"toggledEntities":{"SYS.CORREO":"True"}}
        respSnips = entidadesSnips(event['mensaje'], entidades)
        if respSnips['entity'] == "SYS.CORREO":
            respuesta =dataBot["ResponseVenta"][n_pregunta]
            n_pregunta  += 1
        else:
            respuesta = "Ingresa un correo electronico, recuerda ingresar datos reales. Si tienes otra duda reinicia el chat."
    elif n_pregunta > 3:
        respuesta =dataBot["ResponseVenta"][n_pregunta]
        n_pregunta  += 1
    retorna = {"respuesta": respuesta,"n_pregunta":n_pregunta, "mensaje": event["mensaje"],"estado": estado,"sessionID": event["sessionID"],"intent":"venta"}
    return retorna

#funcion que invoca a snips y sus entidades
def entidadesSnips(mensaje, toggledEntities):
    entity = None; rawValue = None; intent = None
    paramSnips={"bot":"grupovanguardia","message":mensaje}
    paramSnips.update(toggledEntities)
    print(paramSnips)
    respSnips = lambdas.invoke(FunctionName=lambdaSnips,Payload=json.dumps(paramSnips))
    print(respSnips)
    respSnips = json.load(respSnips['Payload'])
    respSnips = respSnips['body']
    print("defSnips ",respSnips)
    if len(respSnips['slots']) > 0:
        for slot in respSnips['slots']:
            if slot['entity'] == 'SYS.NOMBRE':
                print("Result expr: ",re.search(".(\s+?).", slot['rawValue']))
                if (re.search(".(\s+?).", slot['rawValue']) != None):
                    rawValue = slot['rawValue']
                    entity = 'SYS.NOMBRE'
            if slot['entity'] == 'SYS.TELEFONO':
                entity = 'SYS.TELEFONO'
                rawValue = slot['rawValue']
            if slot['entity'] == 'SYS.CORREO':
                entity = 'SYS.CORREO'
                rawValue = slot['rawValue']
    if respSnips['intent']['intentName'] == 'aceptar' and respSnips['intent']['probability'] >= 0.7:
        intent = respSnips['intent']['intentName']
    retorno = {"intent": intent, "entity":entity, "rawValue":rawValue}
    print("returnDefSnips ",retorno)
    return retorno

