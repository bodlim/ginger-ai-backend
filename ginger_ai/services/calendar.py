from typing import Dict
import os
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import json
import anthropic

class AutomatedFamilyAgent:
    def __init__(self):
        self.client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.calendar_service = self._setup_calendar()
        self.config = self._load_config()
    
    def _setup_calendar(self):
        """Setup Google Calendar API connection"""
        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        return build('calendar', 'v3', credentials=creds)
    
    def _load_config(self) -> Dict:
        """Load or create configuration"""
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                return json.load(f)
        return {
            'family_members': {
                'wife': {'calendar_keywords': ['date', 'family', 'spouse']},
                'son': {'calendar_keywords': ['school', 'play', 'son']}
            },
            'locations': {
                'home': {'lat': 0, 'long': 0},  # To be set during setup
                'school': {'lat': 0, 'long': 0}
            }
        }
    
    async def analyze_family_time(self):
        """Automatically analyze family time from calendar"""
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = self.calendar_service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        family_events = []
        for event in events_result.get('items', []):
            for member, details in self.config['family_members'].items():
                if any(keyword in event['summary'].lower() 
                      for keyword in details['calendar_keywords']):
                    family_events.append({
                        'member': member,
                        'event': event['summary'],
                        'start': event['start'].get('dateTime', event['start'].get('date')),
                        'end': event['end'].get('dateTime', event['end'].get('date'))
                    })
        
        return self._generate_insights(family_events)
    
    async def _generate_insights(self, family_events):
        """Generate insights using Claude"""
        events_context = "\n".join([
            f"Event with {e['member']}: {e['event']} on {e['start']}"
            for e in family_events
        ])
        
        response = await self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""Based on these upcoming family events:
                {events_context}
                
                Please provide:
                1. Suggestions for improving quality time
                2. Potential conversation topics
                3. Activity recommendations
                Keep in mind the goal of being a better father/husband."""
            }]
        )
        
        return response.content

    async def suggest_improvements(self):
        """Proactively suggest family time improvements"""
        insights = await self.analyze_family_time()
        # Process insights and generate actionable suggestions
        return insights
