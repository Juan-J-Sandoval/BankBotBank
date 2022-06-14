import json, boto3, os, decimal, os, re
lex = boto3.client('lex-runtime')
lambdas = boto3.client('lambda')
lambdaSnips = os.environ['Snips']
lambdaSemanticDistance = os.environ['SemanticDistance']
lambdaGoogle = os.environ['GoogleSearch']

bucket_name = os.environ['BUCKET_NAME']
bot_data_file = os.environ['BOT_DATA_FILE']
s3 = boto3.resource('s3')
s3.meta.client.download_file(bucket_name,bot_data_file,"/tmp/"+bot_data_file)
f = open("/tmp/"+bot_data_file, "r")
content = f.read()
dataBot = json.loads(content)


def lambda_handler(event, context):
    print(">>> ",event)
    respuesta = ""
    estado = event["estado"]
    intent = ""
    #se envián los datos a lex para analizar su respuesta
    lexJSON = lexBot(event["mensaje"])
    if lexJSON['score'] > 0:
        respuesta=lexJSON['respuesta']
        intent = lexJSON['intent']
        motor='lex'
        score = lexJSON['score']
    else:
        #si lex no tiene respuesta se envía a Snips
        snipsJSON = snips(event["mensaje"])
        if snipsJSON['score'] > 0:
            respuesta=snipsJSON['respuesta']
            intent = snipsJSON['intent']
            motor='snips'
            score = snipsJSON['score']
        else:
            #si snips no tiene respuesta se envía a distancia semantica
            distanciaJSON = distancia(event["mensaje"])
            if distanciaJSON['score'] > 0.4:
                respuesta=distanciaJSON['respuesta']
                intent = distanciaJSON['intent']
                motor='distance'
                score = distanciaJSON['score']
            else:
                #por últimmo si nadie tiene respuesta contesta GoogleSearch
                GoogleJSON = Google(event["mensaje"])
                respuesta = GoogleJSON['respuesta']
                intent = "Default"
                motor='google'
                score = 0
    #verifica el estado en el que debe pasar para la siguiente respuesta TODO
    retornar = {'respuesta':respuesta,'mensaje':event["mensaje"],'estado':estado,'sessionID':event['sessionID'],"n_pregunta":event["n_pregunta"],
        "intent":intent,"motor":motor, "score": score}
    print("<<< ",retornar)
    return retornar

def snips(mensaje):
    snipsIntent = ""
    snipsScore = 0
    snipsRespuesta = ""
    #se configura el json que debe ser envíado a la lambda de snips
    j={"bot":os.environ['BOT_NAME'],"message":mensaje,"toggledEntities":{"SYS.TELEFONO":"True","SYS.NOMBRE":"True"}}
    respSnips = lambdas.invoke(FunctionName=lambdaSnips,Payload=json.dumps(j))
    respSnips = json.load(respSnips['Payload'])
    print("snips ",respSnips)
    respSnips = respSnips['body']
    snipsIntent = respSnips['intent']['intentName']
    #se analiza que la respuesta tenga un escore mayor a 7
    if float(respSnips['intent']['probability']) > 0.80:
        snipsScore=respSnips['intent']['probability']
        for i in dataBot["ResponseData"]:
            if i['name'] == snipsIntent:
                snipsRespuesta=i['response']
    return {'respuesta': snipsRespuesta, 'intent':snipsIntent, 'score':snipsScore}
def lexBot(mensaje):
    lexScore=0
    lexIntent = ""
    lexRespuesta = ""
    #se configura la invocaion a lex
    responseLex = lex.post_text(botName=os.environ['BOT_NAME'],botAlias=os.environ['BOT_ALIAS'],userId="sesionID",inputText=mensaje)
    print("lex ",responseLex)
    #se verifica que no sea una respuesta sin intencion y que su score sea mayor a 7
    if responseLex['dialogState'] != 'ElicitIntent' and responseLex['dialogState'] != 'Failed':
        if float(responseLex['nluIntentConfidence']['score']) > 0.80:
            lexScore= responseLex['nluIntentConfidence']['score']
            lexIntent = responseLex['intentName']
            lexRespuesta = responseLex['message']
    return {'respuesta': lexRespuesta, 'intent':lexIntent, 'score':lexScore}
def distancia(mensaje):
    response = {'respuesta': '', 'intent': '', 'score': 0.3}
    dictResult = {}
    #se mandan todos los vectores que se tengan almacenados en la base de datos
    for i in dataBot["ResponseData"]:
        if len(i['phrases']) > 0:
            print(i['phrases']," tipo: ", type(i['phrases']))
            j={"operation":"distancia","requestText":mensaje,"responseText":i['phrases']}
            respSemDis = lambdas.invoke(FunctionName=lambdaSemanticDistance,Payload=json.dumps(j, default=decimal_default))
            respSemDis = json.load(respSemDis['Payload'])
            print("distancia ",respSemDis)
            respSemDis = respSemDis['body']
            #se guardan las respuestas con un score menor al de 4
            if float(respSemDis['distance']) <= 0.4:
                dictResult.update({i['name']:float(respSemDis['distance'])})
    print(dictResult)
    #se selecciona la mejor respuesta en caso de haber encontrado varias con score menor a 4
    if dictResult != {}:
        max_key = min(dictResult, key = dictResult.get)
        for i in dataBot["ResponseData"]:
            if len(i['name']) == max_key:
                response = {'respuesta': str(i['response']), 'intent': str(i['name']), 'score': str(respSemDis['distance'])}
    return response
def Google(mensaje):
    j={"text": mensaje}
    respGoogle = lambdas.invoke(FunctionName=lambdaGoogle,Payload=json.dumps(j))
    respGoogle = json.load(respGoogle['Payload'])
    print("google ",respGoogle)
    respGoogle = respGoogle['body']
    if str(respGoogle['answer']) != '[NO-REPLY]':
        return {'respuesta': str(respGoogle['answer']),'intent':None, 'score':None}
    else:
        return {'respuesta': "No puedo contestar a tu mensaje, se más especifico",'intent':None, 'score':None}

#funcion que ayuda a configurar los vectores que se le deben enviar a distancia semantica
def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError

