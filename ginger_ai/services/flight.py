from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import aiohttp
import logging
import os


logging.basicConfig(level=logging.INFO)


@dataclass
class FlightSearch:
    origin: str
    destination: str
    departure_date: datetime
    return_date: Optional[datetime] = None
    passengers: Dict[str, int] = None  # e.g., {"adults": 2, "children": 1}


class FlightIntegration:
    def __init__(self):
        self.amadeus_api_key = os.getenv("AMADEUS_API_KEY")
        self.amadeus_api_secret = os.getenv("AMADEUS_API_SECRET")
        self.skyscanner_api_key = os.getenv("SKYSCANNER_API_KEY")
        logging.info("Successful logging of secret for AMADEUS and SKYSCANNER")
        
    async def search_family_friendly_flights(self, search: FlightSearch) -> List[Dict]:
        """Search for family-friendly flights considering factors like timing and layovers"""
        amadeus_results = await self._search_amadeus(search)
        skyscanner_results = await self._search_skyscanner(search)
        
        return self._merge_and_filter_results(
            amadeus_results, 
            skyscanner_results,
            family_friendly_only=True
        )
    
    async def suggest_family_destinations(
        self, budget: float, travel_dates: Dict[str, datetime]
    ) -> List[Dict]:
        """Suggest family-friendly destinations within budget"""
        async with aiohttp.ClientSession() as session:
            # Query multiple APIs for destination suggestions
            destinations = await self._get_destination_suggestions(session, budget)
            return self._filter_family_destinations(destinations)
    
    async def monitor_price_alerts(self, routes: List[Dict]) -> Dict:
        """Monitor price changes for specific routes"""
        alerts = {}
        for route in routes:
            alerts[f"{route['origin']}-{route['destination']}"] = \
                await self._check_price_trends(route)
        return alerts

    def integrate_with_calendar(self, flight_options: List[Dict], 
        calendar_events: List[Dict]) -> List[Dict]:
        """Match flight options with calendar availability"""
        return [
            flight for flight in flight_options
            if self._is_compatible_with_schedule(flight, calendar_events)
        ]


class TravelPlanner:
    def __init__(self, flight_integration: FlightIntegration):
        self.flight_integration = flight_integration
    
    async def plan_family_trip(
        self, 
        budget: float,
        preferred_dates: List[datetime],
        family_size: Dict[str, int]
    ) -> Dict:
        """Plan a complete family trip considering all factors"""
        destinations = await self.flight_integration.suggest_family_destinations(
            budget=budget,
            travel_dates={"start": preferred_dates[0], "end": preferred_dates[-1]}
        )
        
        trips = []
        for dest in destinations:
            flights = await self.flight_integration.search_family_friendly_flights(
                FlightSearch(
                    origin=self.home_airport,
                    destination=dest["airport"],
                    departure_date=preferred_dates[0],
                    return_date=preferred_dates[-1],
                    passengers=family_size
                )
            )
            
            if flights:
                trips.append({
                    "destination": dest,
                    "flights": flights,
                    "total_cost": self._calculate_total_cost(flights),
                    "family_friendly_score": self._calculate_family_score(dest, flights)
                })
        
        return sorted(trips, key=lambda x: x["family_friendly_score"], reverse=True)
    