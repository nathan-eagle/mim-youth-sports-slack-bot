#!/usr/bin/env python3

import json
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

class AIColorService:
    """AI-powered service to convert color names to hex codes"""
    
    @classmethod
    def get_hex_for_colors(cls, color_names: list) -> dict:
        """Use AI to convert color names to hex codes"""
        
        system_prompt = """You are a color expert. Convert color names to accurate hex color codes.
        
        Consider common clothing/textile colors, especially for youth sports merchandise.
        
        Respond in JSON format:
        {
            "color_name_1": "#HEXCODE",
            "color_name_2": "#HEXCODE"
        }
        
        Guidelines:
        - Use standard web-safe colors when possible
        - For "Heather" colors, use slightly muted tones
        - For "Solid" colors, use pure/bright versions
        - Navy should be dark blue (#000080)
        - Royal Blue should be vibrant (#4169E1)
        - Be consistent with common color expectations"""
        
        try:
            color_list = ", ".join(color_names)
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Convert these colors to hex codes: {color_list}"}
                ],
                temperature=0.1  # Low temperature for consistency
            )
            
            result = json.loads(response['choices'][0]['message']['content'])
            return result
            
        except Exception as e:
            print(f"AI color conversion error: {e}")
            # Fallback to basic colors
            return {color: "#808080" for color in color_names}
    
    @classmethod  
    def get_colors_with_ai_hex(cls, color_names: list) -> list:
        """Get colors with AI-generated hex codes"""
        hex_map = cls.get_hex_for_colors(color_names)
        
        return [
            {
                "name": color,
                "hex": hex_map.get(color, "#808080")
            }
            for color in color_names
        ]
    
    @classmethod
    def get_default_colors_for_products(cls, logo_url: str) -> dict:
        """Get AI-recommended default colors for different product types based on logo"""
        
        system_prompt = """You are a youth sports merchandise expert. Analyze the logo/image and recommend appropriate colors for different product types.
        
        Consider:
        - Colors that complement the logo
        - Colors popular with youth sports teams
        - Colors that are appropriate for children/teenagers
        - Colors that work well for team merchandise
        
        Respond in JSON format:
        {
            "success": true,
            "colors": {
                "tshirt": "color_name",
                "hoodie": "color_name", 
                "headwear": "color_name",
                "tank": "color_name",
                "long_sleeve": "color_name"
            }
        }
        
        Use colors like: Black, Navy, White, Red, Blue, Green, Gray, Purple, Orange
        Avoid: Neon colors, hot pink, lime green"""
        
        try:
            user_prompt = f"""Analyze this team logo and recommend colors for youth sports merchandise: {logo_url}
            
            What colors would work best for t-shirts, hoodies, hats, tank tops, and long sleeve shirts for a youth sports team?"""
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            result = json.loads(response['choices'][0]['message']['content'])
            return result
            
        except Exception as e:
            print(f"AI color recommendation error: {e}")
            # Fallback to safe defaults
            return {
                "success": False,
                "error": str(e),
                "colors": {
                    "tshirt": "Black",
                    "hoodie": "Navy", 
                    "headwear": "Black",
                    "tank": "Black",
                    "long_sleeve": "Navy"
                }
            }


# Create singleton instance
ai_color_service = AIColorService()

# Test the AI service
if __name__ == "__main__":
    test_colors = [
        "Royal Blue", "Navy", "Heather Grey", "Forest Green", 
        "Cardinal Red", "Solid White", "Purple Rush"
    ]
    
    print("🤖 AI Color Conversion Test:")
    try:
        ai_service = AIColorService()
        hex_results = ai_service.get_hex_for_colors(test_colors)
        
        for color, hex_code in hex_results.items():
            print(f"   {color}: {hex_code}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")