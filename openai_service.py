import os
import logging
from openai import OpenAI
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def analyze_parent_request(self, message: str, context: str = "") -> Dict:
        """Analyze parent's message to understand their product needs"""
        
        system_prompt = """You are a helpful assistant for a youth sports team merchandise service. 
        Parents message you wanting to customize products for their kids' sports teams.
        
        Available products:
        - Unisex Jersey Short Sleeve Tee (shirt)
        - Unisex Heavy Cotton Tee (shirt)
        - Unisex Softstyle T-Shirt (shirt)
        - Unisex College Hoodie (hoodie)
        - Unisex Midweight Softstyle Fleece Hoodie (hoodie)
        - Unisex Supply Hoodie (hoodie)
        
        Your job is to:
        1. Determine if the parent has specified a product type (shirt, hoodie)
        2. Extract any team/sport information mentioned
        3. Note if they want to upload a logo
        4. Provide a friendly, enthusiastic sports parent response
        
        Respond in JSON format with:
        {
            "product_specified": true/false,
            "product_type": "shirt"|"hoodie"|null,
            "sport_mentioned": "sport name or null",
            "team_mentioned": "team name or null", 
            "wants_logo": true/false,
            "response_message": "friendly response to parent",
            "needs_clarification": true/false
        }"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context: {context}\n\nParent message: {message}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            logger.info(f"OpenAI analysis result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {
                "product_specified": False,
                "product_type": None,
                "sport_mentioned": None,
                "team_mentioned": None,
                "wants_logo": False,
                "response_message": "Hi there! I'd love to help you create custom merchandise for your team. Could you tell me what type of product you're looking for?",
                "needs_clarification": True
            }
    
    def generate_product_clarification(self, available_products: list) -> str:
        """Generate a friendly message asking parents to specify product type"""
        
        system_prompt = """You are a helpful youth sports merchandise assistant. 
        Generate a friendly, enthusiastic message asking a parent to choose from available products.
        Keep it concise and sports-parent friendly."""
        
        products_text = ", ".join(available_products)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Ask parent to choose from these products: {products_text}"}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Which product would you like to customize? We have: {products_text}"
    
    def generate_logo_request_message(self, product_name: str, team_info: str = "") -> str:
        """Generate message asking parent for team logo"""
        
        team_context = f" for {team_info}" if team_info else ""
        
        system_prompt = """You are a helpful youth sports merchandise assistant.
        Generate a friendly, concise message asking a parent to provide their team logo.
        Mention they can upload a file or provide a URL. Keep it enthusiastic and brief."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Ask for team logo for {product_name}{team_context}"}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Great choice on the {product_name}! Please upload your team logo (image file) or provide a URL link to your logo, and I'll customize it for you."

    def get_contextual_response(self, context_prompt: str, user_message: str) -> str:
        """Generate context-aware response using LLM intelligence"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": context_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI contextual response error: {e}")
            return "I'd be happy to help you with your team merchandise! What would you like to create next?"

# Global instance
openai_service = OpenAIService() 