import json

def handler(event, context):
    """
    Simple test function to verify Netlify functions are working
    """
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'message': 'Test function is working!',
            'event': str(event),
            'timestamp': str(context.get('requestTimeEpoch', 'unknown'))
        })
    }
