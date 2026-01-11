"""
Simple RAG (Retrieval-Augmented Generation) system for tourism data.
"""
import json
from typing import List, Dict, Any
from datetime import datetime


class TourismRAG:
    """Simple RAG system for Canary Islands tourism data."""
    
    def __init__(self, data_path: str):
        """
        Initializes the RAG system by loading the data.
        
        Args:
            data_path: Path to JSON file with tourism data
        """
        self.data = self._load_data(data_path)
        self.islands = {
            1: "Tenerife",
            2: "Gran Canaria",
            3: "Lanzarote",
            4: "Fuerteventura",
            5: "La Palma",
            6: "La Gomera",
            7: "El Hierro"
        }
    
    def _load_data(self, data_path: str) -> List[Dict[str, Any]]:
        """Loads data from JSON file."""
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")
            return []
    
    def retrieve_relevant_data(self, query: str, max_results: int = 50) -> str:
        """
        Retrieves relevant data based on user query.
        Simple system that filters by keywords and recency.
        
        Args:
            query: User query
            max_results: Maximum number of records to return
            
        Returns:
            JSON string with most relevant data
        """
        query_lower = query.lower()
        
        # Detect mentioned island
        island_filter = None
        for code, name in self.islands.items():
            if name.lower() in query_lower:
                island_filter = code
                break
        
        # Detect time period
        year_filter = None
        month_filter = None
        current_year = datetime.now().year
        
        # Search for mentioned years
        for year in range(2024, current_year + 1):
            if str(year) in query_lower:
                year_filter = year
                break
        
        # Search for mentioned months (in Spanish)
        months_map = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
            "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
            "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
        }
        
        for month_name, month_num in months_map.items():
            if month_name in query_lower:
                month_filter = month_num
                break
        
        # Filter data
        filtered_data = self.data
        
        if island_filter:
            filtered_data = [d for d in filtered_data if d.get("island_code") == island_filter]
        
        if year_filter:
            filtered_data = [d for d in filtered_data if d.get("year") == year_filter]
        
        if month_filter:
            filtered_data = [d for d in filtered_data if d.get("month") == month_filter]
        
        # If no specific filters, take most recent data
        if not island_filter and not year_filter and not month_filter:
            # Sort by date and take most recent
            filtered_data = sorted(
                self.data,
                key=lambda x: x.get("week_start_date", ""),
                reverse=True
            )[:max_results]
        else:
            # Limit results
            filtered_data = filtered_data[:max_results]
        
        # Detect specific mentioned metrics
        metrics_keywords = {
            "ocupación": "occupancy_rate",
            "turistas": "total_tourists",
            "ingresos": "revenue",
            "gastos": "total_expenditure",
            "tarifa": "avg_daily_rate_eur",
            "noches": "nights",
            "estancia": "stay_length",
            "internacional": "intl_passengers",
            "doméstico": "dom_passengers",
            "eventos": "events_count"
        }
        
        # Add summary statistics if specific metrics are mentioned
        summary = {}
        for keyword, metric in metrics_keywords.items():
            if keyword in query_lower and filtered_data:
                values = [d.get(metric, 0) for d in filtered_data if d.get(metric) is not None]
                if values:
                    summary[metric] = {
                        "average": sum(values) / len(values),
                        "max": max(values),
                        "min": min(values),
                        "total": sum(values) if metric != "occupancy_rate" else None
                    }
        
        # Create structured response
        result = {
            "records": filtered_data,
            "total_records": len(filtered_data),
            "applied_filters": {
                "island": self.islands.get(island_filter) if island_filter else None,
                "year": year_filter,
                "month": month_filter
            },
            "statistical_summary": summary if summary else None
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def get_island_summary(self, island_code: int) -> str:
        """
        Gets a summary for a specific island.
        
        Args:
            island_code: Island code (1-7)
            
        Returns:
            JSON string with island summary
        """
        island_data = [d for d in self.data if d.get("island_code") == island_code]
        
        if not island_data:
            return json.dumps({"error": "No data available for this island"})
        
        # Calculate general statistics
        total_tourists = sum(d.get("total_tourists", 0) for d in island_data)
        avg_occupancy = sum(d.get("occupancy_rate", 0) for d in island_data) / len(island_data)
        total_revenue = sum(d.get("revenue", 0) for d in island_data)
        
        summary = {
            "island": self.islands.get(island_code),
            "code": island_code,
            "general_statistics": {
                "total_tourists": total_tourists,
                "average_occupancy": round(avg_occupancy * 100, 2),
                "total_revenue": round(total_revenue, 2),
                "available_records": len(island_data)
            },
            "latest_data": island_data[-5:]  # Last 5 records
        }
        
        return json.dumps(summary, ensure_ascii=False, indent=2)
