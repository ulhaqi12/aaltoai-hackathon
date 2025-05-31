import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import json

load_dotenv()

class ReportPipelineOrchestrator:
    """Main orchestrator that connects all MCP agents to generate reports from user intent"""
    
    def __init__(self):
        self.reformulate_url = "http://localhost:8071"
        self.intent_to_query_url = "http://localhost:8070" 
        self.api_to_report_url = "http://localhost:8073"
        self.plot_generation="http://localhost:8072"
        
        # Database connection for api-to-report service
        self.postgres_uri = os.getenv("POSTGRES_URI")
    
    async def reformulate_intent(self, original_intent: str) -> str:
        """Call reformulate-intent agent to improve the user's query"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"intent": original_intent}
                async with session.post(f"{self.reformulate_url}/reformulate", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("reformulated_intent", original_intent)
                    else:
                        print(f"Reformulate service error: {response.status}")
                        return original_intent
        except Exception as e:
            print(f"Error calling reformulate service: {e}")
            return original_intent
    
    async def generate_sql_query(self, intent: str) -> Optional[str]:
        """Call intent-to-query agent to generate SQL from intent"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"question": intent}
                async with session.post(f"{self.intent_to_query_url}/ask", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("sql_query")
                    else:
                        print(f"Intent-to-query service error: {response.status}")
                        return None
        except Exception as e:
            print(f"Error calling intent-to-query service: {e}")
            return None
    
    async def generate_report(self, original_intent: str, reformulated_intent: str, sql_query: str) -> Optional[str]:
        """Call api-to-report service to generate final HTML report"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "original_query": original_intent,
                    "reformulated_query": reformulated_intent,
                    "sql_query": sql_query
                }
                async with session.post(f"{self.api_to_report_url}/generate-report", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("html_report")
                    else:
                        error_text = await response.text()
                        print(f"Report generation error: {response.status} - {error_text}")
                        return None
        except Exception as e:
            print(f"Error calling report generation service: {e}")
            return None
    
    async def run_full_pipeline(self, user_intent: str) -> Dict[str, Any]:
        """Run the complete pipeline: Intent -> Reformulate -> SQL -> Report"""
        print(f"🚀 Starting pipeline for: '{user_intent}'")
        
        # Step 1: Reformulate the intent
        print("📝 Step 1: Reformulating intent...")
        reformulated_intent = await self.reformulate_intent(user_intent)
        print(f"   Original: {user_intent}")
        print(f"   Reformulated: {reformulated_intent}")
        
        # Step 2: Generate SQL query
        print("🔍 Step 2: Generating SQL query...")
        sql_query = await self.generate_sql_query(reformulated_intent)
        if not sql_query:
            return {"error": "Failed to generate SQL query", "step": "intent-to-query"}
        print(f"   SQL: {sql_query}")
        
        # Step 3: Generate report
        print("📊 Step 3: Generating report...")
        html_report = await self.generate_report(user_intent, reformulated_intent, sql_query)
        if not html_report:
            return {"error": "Failed to generate report", "step": "api-to-report"}
        
        # Save the report
        report_filename = f"report_{hash(user_intent) % 10000}.html"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        print(f"✅ Pipeline completed! Report saved as: {report_filename}")
        
        return {
            "success": True,
            "original_intent": user_intent,
            "reformulated_intent": reformulated_intent,
            "sql_query": sql_query,
            "report_file": report_filename
        }

async def main():
    """Example usage of the pipeline"""
    orchestrator = ReportPipelineOrchestrator()
    
    # Test with Northwind-specific user intents that will return data
    test_intents = [
        "Show me the top 10 best-selling products by total quantity sold",
        "What are the total sales amounts by customer for our top 10 customers?", 
        "Show me monthly sales trends from 1996 to 1998",
        "Which employees have processed the most orders and what's their total sales volume?",
        "What are the sales by product category showing total revenue per category?"
    ]
    
    for intent in test_intents:
        print("\n" + "="*70)
        result = await orchestrator.run_full_pipeline(intent)
        if result.get("success"):
            print(f"Success! Check: {result['report_file']}")
        else:
            print(f"Error: {result}")
        print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
