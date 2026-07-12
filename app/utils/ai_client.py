import os
from google import genai
from google.genai import types
from flask import current_app

def analyze_expenditure_anomalies(project_title, budget, expended, contractor, details):
    """
    Leverages Gemini to identify non-compliance vectors, 
    overpricing, or administrative anomalies.
    """
    # The client automatically picks up the GEMINI_API_KEY environment variable.
    client = genai.Client()
    
    prompt = f"""
    You are an expert civic auditing AI specializing in the Zambian Public Procurement Authority (ZPPA) frameworks.
    Analyze this allocation anomaly profile for potential corruption or inefficiencies:
    - Project Name: {project_title}
    - Budgeted Amount: ZMW {budget}
    - Amount Expended so far: ZMW {expended}
    - Awarded Contractor: {contractor}
    - Description/Logs: {details}
    
    Provide a professional summary breakdown mapping warning indicators, comparative infrastructure values, 
    and recommendations for civic investigators. Keep your language clear, objective, and easy for ordinary citizens to understand.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2, # Low temperature ensures analytical consistency
            )
        )
        return response.text
    except Exception as e:
        return f"Auditing service temporarily delayed. Internal indicator log: {str(e)}"