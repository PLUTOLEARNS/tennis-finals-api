import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
from typing import Dict, Any, Optional
from models import WimbledonResult
import logging

logger = logging.getLogger(__name__)

class WimbledonScraper:
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'WimbledonAPI/1.0 (Educational Project; titantheven@gmail.com) Python/3.12',
        }
        self.max_content_length = 5 * 1024 * 1024
    
    async def get_wimbledon_result(self, year: int) -> WimbledonResult:
        if not (1877 <= year <= 2030):
            raise ValueError("Invalid year range")
            
        url = f"https://en.wikipedia.org/wiki/{year}_Wimbledon_Championships_%E2%80%93_Men%27s_singles"
        
        if not url.startswith("https://en.wikipedia.org/wiki/"):
            raise ValueError("Invalid URL")
        
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=8, connect=3)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        ) as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        content_length = response.headers.get('content-length')
                        if content_length and int(content_length) > self.max_content_length:
                            raise ValueError("Content too large")
                        
                        html = await response.text()
                        if len(html) > self.max_content_length:
                            raise ValueError("Content too large")
                        
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        result = self._parse_infobox(soup, year)
                        if result:
                            return WimbledonResult(**result)
                        
                        result = self._parse_results_table(soup, year)
                        if result:
                            return WimbledonResult(**result)
                        
                        raise Exception("Could not find final match data")
                    else:
                        raise Exception(f"HTTP {response.status}")
            except asyncio.TimeoutError:
                raise Exception("Request timeout")
            except Exception as e:
                logger.error(f"Scraping error for year {year}: {str(e)}")
                raise Exception("Failed to fetch data")
    
    def _parse_infobox(self, soup: BeautifulSoup, year: int) -> Optional[Dict[str, Any]]:
        try:
            infobox = soup.find('table', class_='infobox')
            if not infobox:
                return None
                
            champion = None
            runner_up = None
            score = None
            
            rows = infobox.find_all('tr')
            for i, row in enumerate(rows[:50]):
                label_cell = row.find('th', class_='infobox-label')
                if label_cell:
                    label = label_cell.get_text().strip().lower()
                    data_cell = row.find('td', class_='infobox-data')
                    
                    if data_cell:
                        if 'champion' in label:
                            links = data_cell.find_all('a')
                            for link in links[:5]:  
                                text = link.get_text().strip()
                                if text and len(text) > 2 and len(text) < 100:
                                    champion = text
                                    break
                        
                        elif 'runner' in label:
                            links = data_cell.find_all('a')
                            for link in links[:5]:
                                text = link.get_text().strip()
                                if text and len(text) > 2 and len(text) < 100:
                                    runner_up = text
                                    break
                        
                        elif 'score' in label:
                            score_text = data_cell.get_text().strip()
                            if len(score_text) < 200:  
                                score_match = re.search(r'(\d+[–−-]\d+(?:\([^)]+\))?(?:\s*,\s*\d+[–−-]\d+(?:\([^)]+\))?)*)', score_text)
                                if score_match:
                                    score = score_match.group(1).strip()
            
            if champion and runner_up and score:
                return self._create_result(year, champion, runner_up, score)
            
        except Exception as e:
            logger.error(f"Error parsing infobox: {str(e)}")
        
        return None
    
    def _parse_results_table(self, soup: BeautifulSoup, year: int) -> Optional[Dict[str, Any]]:
        try:
            tables = soup.find_all('table', class_='wikitable')
            for table in tables[:10]:
                rows = table.find_all('tr')
                for row in rows[:20]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        text = ' '.join(cell.get_text() for cell in cells).lower()
                        if 'final' in text:
                            links = row.find_all('a')
                            if len(links) >= 2:
                                champion = links[0].get_text().strip()
                                runner_up = links[1].get_text().strip()
                                
                                if (len(champion) > 2 and len(champion) < 100 and 
                                    len(runner_up) > 2 and len(runner_up) < 100):
                                    
                                    for cell in cells:
                                        cell_text = cell.get_text()
                                        if re.search(r'\d+[–−-]\d+', cell_text) and len(cell_text) < 200:
                                            return self._create_result(year, champion, runner_up, cell_text.strip())
        
        except Exception as e:
            logger.error(f"Error parsing results table: {str(e)}")
        
        return None
    
    def _create_result(self, year: int, champion: str, runner_up: str, score: str) -> Dict[str, Any]:
        champion = re.sub(r'[<>"\']', '', champion.strip())[:100]
        runner_up = re.sub(r'[<>"\']', '', runner_up.strip())[:100]
        score = re.sub(r'[<>"\']', '', score.strip())[:200]
        
        score = re.sub(r'[–−]', '–', score)
        score = re.sub(r'\s+', ' ', score).strip()
        
        sets = len([s for s in score.split(',') if s.strip()])
        tiebreak = '(' in score
        if not champion or not runner_up or not score:
            raise ValueError("Invalid match data")
        
        return {
            'year': year,
            'champion': champion,
            'runner_up': runner_up,
            'score': score,
            'sets': sets,
            'tiebreak': tiebreak
        }
