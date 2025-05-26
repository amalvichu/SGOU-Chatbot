import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class ProgramModel:
    def __init__(self):
        self.api_url = 'http://192.168.20.3:8000/api/programmes'
        self.api_key = '$2y$10$M0JLrgVmX2AUUqMZkrqaKOrgaMMaVFusOVjiXkVjc1YLyqcYFY9Bi'
        self.cache = {}
        self.cache_duration = timedelta(minutes=5)
        self.last_fetch = None

    def _is_cache_valid(self) -> bool:
        """Check if the cached data is still valid."""
        if not self.last_fetch:
            return False
        return datetime.now() - self.last_fetch < self.cache_duration

    def fetch_programs(self) -> List[Dict]:
        """Fetch programs from API with caching."""
        if self._is_cache_valid():
            return self.cache.get('programs', [])

        try:
            headers = {'X-API-KEY': self.api_key}
            response = requests.get(self.api_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if 'programme' in data:
                self.cache['programs'] = data['programme']
                self.last_fetch = datetime.now()
                return self.cache['programs']
            return []

        except requests.exceptions.RequestException as e:
            print(f'Error fetching programs: {str(e)}')
            return self.cache.get('programs', [])

    def get_program_by_name(self, name: str) -> Optional[Dict]:
        """Find a program by its name."""
        programs = self.fetch_programs()
        return next((prog for prog in programs if prog.get('name', '').lower() == name.lower()), None)

    def get_program_by_id(self, program_id: str) -> Optional[Dict]:
        """Find a program by its ID."""
        programs = self.fetch_programs()
        return next((prog for prog in programs if str(prog.get('id')) == str(program_id)), None)

    def search_programs(self, query: str) -> List[Dict]:
        """Search programs by a query string."""
        programs = self.fetch_programs()
        query = query.lower()
        return [prog for prog in programs if query in prog.get('name', '').lower()]

    def format_program_info(self, program: Dict) -> str:
        """Format program information for display."""
        if not program:
            return 'Program not found.'

        info = [f"Program: {program.get('name', 'N/A')}"]
        
        # Add additional fields if they exist
        for field in ['description', 'duration', 'start_date', 'end_date']:
            if program.get(field):
                info.append(f"{field.replace('_', ' ').title()}: {program[field]}")

        return '\n'.join(info)