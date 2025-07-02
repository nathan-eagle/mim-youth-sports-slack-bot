#!/usr/bin/env python3

import json
from openai_service import openai_service

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
            response = openai_service.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Convert these colors to hex codes: {color_list}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1  # Low temperature for consistency
            )
            
            result = json.loads(response.choices[0].message.content)
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