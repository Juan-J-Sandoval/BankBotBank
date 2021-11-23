import boto3, json, os, io, yaml, time
from yaml import Loader
from snips_nlu import SnipsNLUEngine
from snips_nlu.default_configs import CONFIG_ES

lex = boto3.client('lex-models')
nlu_engine = SnipsNLUEngine(config=CONFIG_ES)
s3 = boto3.resource('s3')

bucket_name = os.environ['BUCKET_NAME']
bot_data_file = os.environ['BOT_DATA_FILE']
bot_name = os.environ['BOT_NAME']


def lambda_handler(event, context):
    payload_dictionary = json.loads(json.dumps(event['payload']))
    operation = event['operation']

    if operation == 'trainer':
        result = trainer(payload_dictionary)
    elif operation=='getData':
        result = getData()
    # print("THE BUCKET NAME IS: " + bucket_name)
    # yaml_path = "/tmp/"+ event['bot'] + ".yaml"
    # json_path = "/tmp/"+ event['bot'] + ".json"

    # # se descarga el yaml de entrenamiento
    # s3.meta.client.download_file(bucket_name, event['bot'] + ".yaml", yaml_path)
    
    # # Comando para ejecutar y transformar yaml a json
    # comando = "snips-nlu generate-dataset es "+yaml_path+" > "+json_path
    # os.system(comando)

    # print("reading model at {}".format(json_path))
    # with io.open(json_path) as f:
    #     trainingdata = json.load(f)

    #     #creamos el engine de nlu con el cual vamos a entrenar el modelo
    #     print("training model")
    #     nlu_engine.fit(trainingdata)
    
    # #Placing the byte file in the S3 bucket
    # trained_model = nlu_engine.to_byte_array()
    # print("guardando modelo")
    # s3.meta.client.put_object(Bucket=bucket_name,Key=event['bot'] + "_model.json",Body=trained_model)
    return result

def trainer(payload):
    return {
        "statusCode": 200,
        "body":{"status": "reentrenado"}
    }

def getData():
    #Snips
    SnipsData=[]
    s3.meta.client.download_file(bucket_name,bot_name+'.yaml',"/tmp/"+bot_name+'.yaml')
    with open("/tmp/"+bot_name+'.yaml') as f:
        for data in yaml.load_all(f, Loader=Loader):
            SnipsData.append(data)
    #DistanciaSemantica
    s3.meta.client.download_file(bucket_name,bot_data_file,"/tmp/"+bot_data_file)
    f = open("/tmp/"+bot_data_file, "r")
    content = f.read()
    dataBotDS = json.loads(content)
    #Lex
    s3.meta.client.download_file(bucket_name,bot_name+'.json',"/tmp/"+bot_name+'.json')
    f = open("/tmp/"+bot_name+'.json', "r")
    content = f.read()
    dataBotLex = json.loads(content)
    #Generador de Json unificado
    examples=[]
    jsonUnificado={"intent":[],"entity":[]}
    print("snips>> ",SnipsData)
    print("DS>> ",dataBotDS['ResponseData'])
    print("lex>> ",dataBotLex['resource']["intents"])
    for item in SnipsData:
        for itemDS in dataBotDS['ResponseData']:
            if itemDS['name']==item['name']:
                for itemL in dataBotLex['resource']["intents"]:
                    if itemL['name']==item['name']:
                        examples.extend(item["utterances"])
                        examples.extend(itemL["sampleUtterances"])
                        temp={"name":item['name'],"examples":examples,"response":itemDS["response"],"lexemas":itemDS["phrases"]}
                        print("temp>> ",temp)
                        jsonUnificado["intent"].append(temp)
                        examples=[]
    response={"snips":SnipsData,"DS":dataBotDS['ResponseData'],"lex":dataBotLex['resource']}
    return {
        "statusCode": 200,
        "body":jsonUnificado
    }

def lex(payload):
    print('>>> ',payload)
    #Extrae el zip del bucket 
    s3Response = s3.get_object(Bucket=payload['bucket'],Key=payload['zip'])
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