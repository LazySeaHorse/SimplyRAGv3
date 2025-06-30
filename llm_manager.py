import openai
import google.generativeai as genai
import requests
import json
from typing import List, Dict
from config import Config

class LLMManager:
    def __init__(self):
        # Initialize OpenAI
        if Config.OPENAI_API_KEY:
            openai.api_key = Config.OPENAI_API_KEY
        
        # Initialize Google Gemini
        if Config.GOOGLE_API_KEY:
            genai.configure(api_key=Config.GOOGLE_API_KEY)
    
    def query_openai(self, messages: List[Dict[str, str]]) -> str:
        """Query OpenAI GPT model."""
        try:
            client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error with OpenAI: {str(e)}"
    
    def query_gemini(self, messages: List[Dict[str, str]]) -> str:
        """Query Google Gemini model."""
        try:
            model = genai.GenerativeModel(Config.GEMINI_MODEL)
            
            # Convert messages to Gemini format
            prompt = ""
            for msg in messages:
                if msg["role"] == "system":
                    prompt += f"System: {msg['content']}\n\n"
                elif msg["role"] == "user":
                    prompt += f"User: {msg['content']}\n\n"
            
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error with Gemini: {str(e)}"
    
    def query_github_models(self, messages: List[Dict[str, str]]) -> str:
        """Query GitHub Models."""
        try:
            headers = {
                "Authorization": f"token {Config.GITHUB_TOKEN}",
                "Content-Type": "application/json"
            }
            
            # GitHub Models uses OpenAI-compatible API
            url = f"https://models.inference.ai.azure.com/chat/completions"
            
            data = {
                "model": Config.GITHUB_MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error with GitHub Models: {str(e)}"
    
    def query_lm_studio(self, messages: List[Dict[str, str]]) -> str:
        """Query local LM Studio model."""
        try:
            url = f"{Config.LM_STUDIO_ENDPOINT}/chat/completions"
            
            data = {
                "model": Config.LM_STUDIO_MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error with LM Studio: {str(e)}"
    
    def generate_response(self, model_choice: str, system_prompt: str, context: str, user_query: str) -> str:
        """Generate response using selected model."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_query}"}
        ]
        
        if model_choice == "OpenAI GPT":
            return self.query_openai(messages)
        elif model_choice == "Google Gemini":
            return self.query_gemini(messages)
        elif model_choice == "GitHub Models":
            return self.query_github_models(messages)
        elif model_choice == "LM Studio (Local)":
            return self.query_lm_studio(messages)
        else:
            return "Invalid model selection"