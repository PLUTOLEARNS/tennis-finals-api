import json
import requests
from bs4 import BeautifulSoup
import re

def handler(event, context):
    """
    Main handler for all API endpoints
    """
    try:
        # Set CORS headers
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Content-Type': 'application/json'
        }
        
        # Handle OPTIONS preflight request
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': ''
            }
        
        # Get the path from the event - try multiple possible locations
        path = event.get('path', '/')
        raw_url = event.get('rawUrl', '')
        query_params = event.get('queryStringParameters') or {}
        
        # Debug: Check what we're getting
        debug_info = {
            'path': path,
            'rawUrl': raw_url,
            'queryParams': query_params,
            'event_keys': list(event.keys())
        }
        
        # Determine endpoint from path or rawUrl
        if 'wimbledon' in path or 'wimbledon' in raw_url:
            endpoint = 'wimbledon'
        elif 'health' in path or 'health' in raw_url:
            endpoint = 'health'
        else:
            endpoint = 'root'
        
        # Handle different endpoints
        if endpoint == 'root':
            # Root endpoint
            response_body = {
                "message": "Tennis Finals API",
                "description": "Get Tennis Championship Final Results",
                "version": "1.0.0",
                "debug": debug_info,
                "endpoints": {
                    "root": "/",
                    "wimbledon": "/wimbledon?year=YYYY",
                    "health": "/health"
                },
                "example": "https://inspiring-concha-308678.netlify.app/wimbledon?year=2023"
            }
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(response_body)
            }
        
        elif endpoint == 'wimbledon':
            # Wimbledon endpoint
            year_param = query_params.get('year')
            
            if not year_param:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'error': 'Year parameter is required. Example: /wimbledon?year=2023',
                        'debug': debug_info
                    })
                }
            
            try:
                year = int(year_param)
                if year < 1877 or year > 2030:
                    return {
                        'statusCode': 400,
                        'headers': headers,
                        'body': json.dumps({'error': 'Year must be between 1877 and 2030'})
                    }
                
                # Scrape Wikipedia for tennis data
                url = f"https://en.wikipedia.org/wiki/{year}_Wimbledon_Championships_%E2%80%93_Men%27s_singles"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Parse the data
                infobox = soup.find('table', class_='infobox')
                if infobox:
                    champion = None
                    runner_up = None
                    score = None
                    
                    rows = infobox.find_all('tr')
                    for row in rows:
                        text = row.get_text()
                        if 'Champion' in text:
                            link = row.find('a')
                            if link:
                                champion = link.get_text().strip()
                        elif 'Runner-up' in text:
                            link = row.find('a')
                            if link:
                                runner_up = link.get_text().strip()
                        elif 'Score' in text:
                            score_match = re.search(r'(\d+[–−-]\d+(?:\([^)]+\))?(?:\s*,\s*\d+[–−-]\d+(?:\([^)]+\))?)*)', text)
                            if score_match:
                                score = score_match.group(1).strip()
                    
                    if champion and runner_up and score:
                        sets = len([s for s in score.split(',') if s.strip()])
                        tiebreak = '(' in score
                        
                        response_body = {
                            "year": year,
                            "champion": champion,
                            "runner_up": runner_up,
                            "score": score,
                            "sets": sets,
                            "tiebreak": tiebreak
                        }
                        
                        return {
                            'statusCode': 200,
                            'headers': headers,
                            'body': json.dumps(response_body)
                        }
                
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': f'Data not found for year {year}'})
                }
                
            except ValueError:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Invalid year format. Must be a number.'})
                }
            except Exception as e:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': f'Failed to fetch data for year {year}: {str(e)}'})
                }
        
        elif endpoint == 'health':
            # Health check endpoint
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'status': 'healthy', 
                    'timestamp': str(context.get('requestTimeEpoch', 'unknown')),
                    'debug': debug_info
                })
            }
        
        else:
            # Default response for unknown paths
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Endpoint not found',
                    'available_endpoints': [
                        '/',
                        '/wimbledon?year=YYYY',
                        '/health'
                    ]
                })
            }
    
    except Exception as e:
        # Generic error handler
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }
