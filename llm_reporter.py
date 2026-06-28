import os
import threading
from groq import Groq
from dotenv import load_dotenv

class LLMReporter:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GROQ_API_KEY")
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None
            
    def generate_report(self, simulation_logs, callback):
        """Generates the report in a background thread and calls callback with result."""
        def run():
            if not self.client:
                callback("Error: GROQ_API_KEY environment variable not found. Please set it in a .env file or system variables.")
                return
                
            prompt = f"""
            Act as a Senior Energy Systems Analyst at Tesla.
            Based on the following weekly Vehicle-to-Grid (V2G) simulation logs, generate a highly professional, realistic, and insightful executive summary (3-4 sentences). Focus on the financial and grid-stabilization impacts of the V2G optimization strategy. Avoid overly enthusiastic or robotic language; keep the tone grounded, analytical, and tailored for a corporate energy report.
            
            Key Metrics:
            - Energy Discharged to Grid (Peak): {simulation_logs['total_energy_discharged']:.2f} kWh
            - Energy Charged (Off-Peak): {simulation_logs['total_energy_charged']:.2f} kWh
            - Grid Support Events: {simulation_logs['grid_support_events']}
            - Estimated V2G Earnings: ${simulation_logs['earnings']:.2f}
            - Total Charging Cost: ${simulation_logs['cost']:.2f}
            """
            
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model="llama-3.1-8b-instant",
                )
                callback(chat_completion.choices[0].message.content)
            except Exception as e:
                callback(f"Error generating report: {str(e)}")

        thread = threading.Thread(target=run)
        thread.start()
