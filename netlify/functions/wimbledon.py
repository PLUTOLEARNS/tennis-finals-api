import json
import requests
from bs4 import BeautifulSoup
import re

def handler(event, context):
    """
    Main handler for Wimbledon API endpoints
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
        
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        year_param = query_params.get('year')
        
        if not year_param:
            # Return API information if no year is provided
            response_body = {
                "message": "Tennis Finals API",
                "description": "Get Tennis Championship Final Results",
                "version": "1.0.0",
                "usage": "Add ?year=YYYY to get Wimbledon final results",
                "example": "https://inspiring-concha-308678.netlify.app/.netlify/functions/wimbledon?year=2023",
                "valid_years": "1877-2030"
            }
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(response_body)
            }
        
        # Process the year parameter
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
