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
        - Unisex College Hoodie (hoodie)
        
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

    def analyze_color_request(self, user_request: str, logo_url: str, available_colors: list, product_name: str) -> Dict:
        """Use AI to analyze user's color request and match it to available colors with logo context"""
        
        system_prompt = f"""You are an expert color analyst for youth sports merchandise. 
        
        A parent has uploaded a team logo and is requesting a specific color for their {product_name}.
        
        Your job is to:
        1. Analyze the user's color request in the context of their team logo
        2. Consider the logo's colors when they mention "same color as logo" or "similar to logo"
        3. Match their request to the best available color option
        4. Provide reasoning for your choice
        
        Available colors for {product_name}: {', '.join(available_colors)}
        
        Logo URL: {logo_url}
        
        Consider these guidelines:
        - If they mention "same as logo" or "like in logo", try to match prominent logo colors
        - "Light blue", "aqua", "sky blue" typically map to lighter blue variants
        - "Navy", "dark blue" map to darker blue variants  
        - Be intelligent about color synonyms (e.g., "canvas red" = red)
        - Choose the closest available match if exact color isn't available
        
        Respond in JSON format:
        {{
            "best_color_match": "exact color name from available list",
            "confidence": "high|medium|low",
            "reasoning": "brief explanation of why this color was chosen",
            "logo_colors_considered": "brief description of logo colors if relevant"
        }}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User's color request: '{user_request}'"}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            logger.info(f"AI color analysis result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI color analysis error: {e}")
            # Fallback to first available color
            return {
                "best_color_match": available_colors[0] if available_colors else "Black",
                "confidence": "low", 
                "reasoning": "AI analysis failed, using fallback color",
                "logo_colors_considered": "Unable to analyze due to error"
            }

    def get_logo_inspired_colors(self, logo_url: str, available_colors: list, product_name: str) -> Dict:
        """Use AI to select top 6 colors that would look best with the logo for a specific product"""
        
        system_prompt = f"""You are an expert color consultant for youth sports merchandise.
        
        A team has uploaded a logo and wants to see the best color options for their {product_name}.
        
        Your job is to:
        1. Analyze the logo's color palette and overall aesthetic
        2. Select the top 6 colors from available options that would look best with this logo
        3. Consider both colors that match the logo and complementary colors that would look good
        4. Prioritize colors that are popular for youth sports teams
        
        Logo URL: {logo_url}
        Available colors for {product_name}: {', '.join(available_colors)}
        
        Consider these guidelines:
        - Include colors that directly match prominent logo colors
        - Include complementary colors that work well with the logo
        - Consider classic sports colors (navy, black, white, red, royal blue)
        - Think about what a parent would want for their kid's team
        - Prioritize versatile colors that work for both boys and girls
        
        Respond in JSON format:
        {{
            "top_6_colors": ["color1", "color2", "color3", "color4", "color5", "color6"],
            "reasoning": "brief explanation of color selection strategy",
            "logo_color_analysis": "brief description of the logo's color palette"
        }}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "text",
                                "text": f"Please analyze this logo and select the top 6 colors for {product_name} that would work best with it."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": logo_url
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            logger.info(f"AI logo-inspired colors for {product_name}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI logo color analysis error: {e}")
            # Fallback to first 6 available colors
            fallback_colors = available_colors[:6] if len(available_colors) >= 6 else available_colors
            return {
                "top_6_colors": fallback_colors,
                "reasoning": "AI analysis failed, using fallback colors",
                "logo_color_analysis": "Unable to analyze due to error"
            }

    def analyze_product_request(self, user_request: str, available_products: list) -> Dict:
        """Use AI to analyze user's product request and match it to available products"""
        
        system_prompt = f"""You are an expert product analyst for youth sports merchandise.
        
        A parent is requesting a specific product type for their team merchandise.
        
        Your job is to:
        1. Analyze the user's product request 
        2. Match their request to the best available product from the list
        3. Consider product names, descriptions, and user intent
        4. Provide reasoning for your choice
        
        Available products:
        {chr(10).join([f"- ID: {p['id']}, Name: {p['title']}, Category: {p.get('category', 'unknown')}" for p in available_products])}
        
        Consider these guidelines:
        - Match based on product type (shirt, hoodie, etc.)
        - Pay attention to specific product features mentioned (jersey, heavy cotton, softstyle, midweight, fleece, etc.)
        - Consider synonyms (sweatshirt = hoodie, tee = shirt, etc.)
        - Choose the most specific match when possible
        - Default to popular options if request is vague
        
        Respond in JSON format:
        {{
            "best_product_match": "product_id",
            "confidence": "high|medium|low",
            "reasoning": "brief explanation of why this product was chosen",
            "product_type_detected": "shirt|hoodie|other"
        }}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User's product request: '{user_request}'"}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            logger.info(f"AI product analysis result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI product analysis error: {e}")
            # Fallback to first available product
            fallback_product = available_products[0] if available_products else None
            return {
                "best_product_match": fallback_product['id'] if fallback_product else "12",
                "confidence": "low",
                "reasoning": "AI analysis failed, using fallback product",
                "product_type_detected": "unknown"
            }

# Global instance
openai_service = OpenAIService() 