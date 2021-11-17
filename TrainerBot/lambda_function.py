import boto3, json, os, io
from snips_nlu import SnipsNLUEngine
from snips_nlu.default_configs import CONFIG_ES
bucket_name = os.getenv('MODEL_BUCKET_NAME', "")
nlu_engine = SnipsNLUEngine(config=CONFIG_ES)
s3 = boto3.resource('s3')

bucket_name = os.environ['BUCKET_NAME']
bot_data_file = os.environ['BOT_DATA_FILE']
s3.download_file(bucket_name,bot_data_file,"/tmp/"+bot_data_file)
f = open("/tmp/"+bot_data_file, "r")
content = f.read()
dataBotDS = json.loads(content)

def lambda_handler(event, context):
    payload_dictionary = json.loads(json.dumps(event['payload']))
    operation = event['operation']

    if operation == 'trainer':
        result = trainer(payload_dictionary)
    elif operation=='retraining':
        result = retraining(payload_dictionary)
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
    return {
        "statusCode": 200,
        "body": {"status": "ok"}
    }

def retraining(payload):
    return {
        "statusCode": 200,
        "body":{"status": "reentrenado"}
    }

def trainer(payload):
    return {
        "statusCode": 200,
        "body":{"status": "entrenado"}
    }