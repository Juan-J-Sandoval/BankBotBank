import io
import json
from snips_nlu import load_resources, SnipsNLUEngine
import os
import boto3
#TODO TEMPORARY IMPORT
import re

#TODO SYSTEM EXPRESSIONS ARE PROCESSED IN THE SAME INTENT PROCESSOR FUNCTION. IT SHOULD BE SPLIT INTO A DIFFERENT FUNCTION AND CALLED FROM THERE

#This version is set to one that will never correspond to the version stored, because no version is stored locally,
#so that it always downloads the latest when the function is first instanced.
latest_version = ""
bucket_name = os.getenv('MODEL_BUCKET_NAME', "")
nlu_engine = SnipsNLUEngine()
lambdas = boto3.client('lambda')

#Default toggle keys and values for when a dictionary isn't sent by the user, or, the dictioanary to compare to when certain values are missing in the entire list
defaultEntityToggles = {"SYS.TIEMPO":"True","SYS.MONEDA":"True","SYS.CP":"True","SYS.TELEFONO":"True","SYS.FECHA":"True","SYS.PORCENTAJE":"True","SYS.CORREO":"True","SYS.URL":"True","SYS.NUMERO.VUELO":"True","SYS.DURACION":"True","SYS.NOMBRE":"True","SYS.ORGANIZACION":"True","SYS.LOCACION":"True"}

def lambda_handler(event, context):
    global nlu_engine
    lambdas = boto3.client('lambda')

    #temporal variable while we get it form the request, defining grupovanguardia as default bot
    bot = None
    message = None
    toggledEntities = None
    print("EVENT: " + str(event))
    try:
        body = json.loads(event.get('body', '{}'))
    except Exception as e:
        print("Exception: " + str(e))

    try:
        print("REQUEST BODY: " + str(body))
    except Exception as e:
        print("Exception printing 1: " + str(e))
    try:
        message = event['message']
        bot = event['bot']
        try:
            toggledEntities = event['toggledEntities']
            print("ENTITIES TOGGLED: "+ str(toggledEntities))
        except Exception as e:
            toggledEntities = False
            print("No entities specified")

        print("MESSAGE: " + message)
        print("bot: " + bot)
    except Exception as e:
        print("Exception printing 2: " + str(e))
    #We load the bot with the provided specification
    load_latest_model(bot)

    #We parse the message to get the intent classification.
    try:
        response = nlu_engine.parse(message)
    except Exception as e:
        print("Exception response: " + str(e))
    payload = {}
    payload.update(event)
    response = {'response':response}
    payload.update(response)
    payload = json.dumps(payload)
    print(type(payload)," ",payload)
    response = lambdas.invoke(
        FunctionName=os.getenv('ENTIDADESPLN'),
        InvocationType='RequestResponse',
        Payload=payload
    )
    datosEntidadesPLN = response['Payload'].read()
    respuesta = json.loads(datosEntidadesPLN)
    return {
        "statusCode": 200,
        "body": respuesta
    }



def load_latest_model(bot):
    global latest_version
    global bucket_name
    print("THE BUCKET NAME IS: " + bucket_name)

    if len(bucket_name) > 0:
        #client = boto3.client('s3',aws_access_key_id="AKIA6G4VNHQWPFDXJLQV",aws_secret_access_key="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")
        client = boto3.client('s3')
        response = client.head_object(Bucket=bucket_name, Key=bot + "_model.json")
        print("S3 RESPONSE: " + str(response))

        print("model version: {}".format(latest_version))
        current_version = response.get('VersionId', response.get("LastModified", "0"))
        print("current version: {}".format(current_version))

        if latest_version != current_version:
            latest_version = current_version
            print("not latest version")
    else:
        raise Exception("Config bucket is undefined")

    download_model(latest_version, bot)

##
# Sets the latest model to be able to download it.
# @param  bot           {string} the name of the bot to which the data corresponds
# @param  model_version {str}    corresponding version to download.
# Results in running load_model()
##
def download_model(model_version, bot):
    global bucket_name
    model_file = "{}.json".format(model_version)
    print("model file: " + str(model_file))

    model_file_path = "/tmp/models/{}".format(model_file)
    print("model file path: " + str(model_file_path))

    #We see if the file exists locally
    if not os.path.isfile(model_file_path):
        print("model file doesn't exist, downloading new model to {}".format(model_file_path))

        #s3 = boto3.resource('s3', aws_access_key_id="AKIA6G4VNHQWPFDXJLQV",aws_secret_access_key="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")
        s3 = boto3.resource('s3')

        if not os.path.exists('/tmp/models'):
            os.makedirs('/tmp/models')

        #we download the pretrained model to the specified model_file_path
        s3.meta.client.download_file(bucket_name, bot + "_model.json", model_file_path)

    load_model(model_file_path)

##
# Sets the latest model to be able to download it.
# @param  model_file_path {string} the local path of the downloaded model to load to the engine.
# Results in the engine loaded with the model ready to make inferences.
##
def load_model(model_file_path):
    global nlu_engine
    print("reading model at {}".format(model_file_path))
    with io.open(model_file_path, 'r+b') as f:
        model = f.read()
        nlu_engine = SnipsNLUEngine.from_byte_array(model)
