import json, os
def lambda_handler(event, context):
    #solo para verificar la conexion 
    print(json.dumps(event))
    return {}