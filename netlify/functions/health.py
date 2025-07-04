import json

def lambda_handler(event, context):
    """
    Health check function
    """
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Content-Type': 'application/json'
    }
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'status': 'healthy', 
            'message': 'Tennis API is running',
            'timestamp': str(context.get('requestTimeEpoch', 'unknown'))
        })
    }

# Also export as handler for compatibility
handler = lambda_handler
