import json
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from tennis_scraper import TennisScraper
    from models import TennisResult
except ImportError:
    # Fallback for deployment
    import requests
    from bs4 import BeautifulSoup
    import re
    
    class TennisResult:
        def __init__(self, year, champion, runner_up, score, sets, tiebreak):
            self.year = year
            self.champion = champion
            self.runner_up = runner_up
            self.score = score
            self.sets = sets
            self.tiebreak = tiebreak
    
    class TennisScraper:
        def get_tennis_result(self, year: int) -> TennisResult:
            url = f"https://en.wikipedia.org/wiki/{year}_Wimbledon_Championships_%E2%80%93_Men%27s_singles"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Basic parsing logic
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
                    return TennisResult(
                        year=year,
                        champion=champion,
                        runner_up=runner_up,
                        score=score,
                        sets=sets,
                        tiebreak=tiebreak
                    )
            
            raise Exception("Could not find data")

scraper = TennisScraper()

def handler(event, context):
    """
    Netlify function handler for the Tennis API
    """
    try:
        # Get the HTTP method and path
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        query_params = event.get('queryStringParameters') or {}
        
        # Set CORS headers
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Content-Type': 'application/json'
        }
        
        # Handle OPTIONS preflight request
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': ''
            }
        
        # Route handling
        if path == '/' or path == '/app':
            # Root endpoint
            response_body = {
                "message": "Tennis Finals API",
                "description": "Get Tennis Championship Final Results",
                "endpoints": {
                    "wimbledon": "/wimbledon?year=YYYY",
                    "health": "/health"
                }
            }
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(response_body)
            }
        
        elif path == '/wimbledon':
            # Wimbledon endpoint
            year_param = query_params.get('year')
            if not year_param:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Year parameter is required'})
                }
            
            try:
                year = int(year_param)
                if year < 1877 or year > 2030:
                    return {
                        'statusCode': 400,
                        'headers': headers,
                        'body': json.dumps({'error': 'Invalid year range'})
                    }
                
                result = scraper.get_tennis_result(year)
                response_body = {
                    "year": result.year,
                    "champion": result.champion,
                    "runner_up": result.runner_up,
                    "score": result.score,
                    "sets": result.sets,
                    "tiebreak": result.tiebreak
                }
                
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps(response_body)
                }
            
            except ValueError:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Invalid year format'})
                }
            except Exception as e:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': f'Data not available for year {year}'})
                }
        
        elif path == '/health':
            # Health check endpoint
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'status': 'healthy'})
            }
        
        else:
            # 404 for unknown paths
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Endpoint not found'})
            }
    
    except Exception as e:
        # Generic error handler
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }
