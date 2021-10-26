import json, boto3, os, decimal
from boto3.dynamodb.conditions import Key
dynamodb = boto3.resource('dynamodb')
tabla = dynamodb.Table(os.environ['DBTableName'])


def lambda_handler(event, context):
    dataBot = tabla.query(
        KeyConditionExpression=Key('IdBot').eq(event['NameBot'])
    )
    dataBot['Items'][0]['EvaluationData']['ConversationTests'].append(event['NewData'])
    itemNew = dataBot['Items'][0]
    response = tabla.put_item(
        Item=itemNew
    )
    print(response)
    return {
        'statusCode': 200,
        'body': 'Saved Data'
    }
