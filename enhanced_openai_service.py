#!/usr/bin/env python3
"""
Enhanced OpenAI Service with Improved Color Detection

This module enhances the existing OpenAI service with better color detection
and multi-color handling based on the validation testing results.
"""

import os
import logging
import re
from openai import OpenAI
from typing import Dict, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class EnhancedOpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.color_families = {
            "red": ["red", "maroon", "burgundy", "crimson", "scarlet", "cherry"],
            "blue": ["blue", "navy", "royal blue", "royal", "cobalt", "azure"],
            "green": ["green", "forest", "lime", "emerald", "sage", "olive"],
            "black": ["black", "charcoal", "onyx"],
            "white": ["white", "ivory", "cream", "off-white"],
            "orange": ["orange", "rust", "burnt", "tangerine"],
            "yellow": ["gold", "yellow", "golden", "amber", "sunshine"],
            "purple": ["purple", "violet", "lavender", "magenta"],
            "gray": ["gray", "grey", "silver", "slate"],
            "pink": ["pink", "rose", "blush", "coral"],
            "brown": ["brown", "tan", "khaki", "beige", "chocolate"]
        }
        
    def analyze_parent_message(self, message: str, context: str = "") -> Dict:
        """Enhanced parent message analysis with better color detection"""
        
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
        4. Identify primary and secondary colors mentioned
        5. Provide a friendly, enthusiastic sports parent response
        
        For color detection, prioritize the first color mentioned or colors preceded by words like "mainly", "primarily", "prefer".
        
        Respond in JSON format with:
        {
            "product_specified": true/false,
            "product_type": "shirt"|"hoodie"|null,
            "sport_mentioned": "sport name or null",
            "team_mentioned": "team name or null", 
            "wants_logo": true/false,
            "primary_color": "primary color mentioned or null",
            "secondary_colors": ["list of other colors mentioned"],
            "color_context": "single_color"|"multiple_colors"|"color_preference"|"logo_based",
            "response_message": "friendly response to parent",
            "needs_clarification": true/false
        }"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Parent message: {message}\nContext: {context}"}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Enhance with local color analysis as backup
            local_color_analysis = self._analyze_colors_locally(message)
            if not result.get('primary_color') and local_color_analysis.get('primary_color'):
                result['primary_color'] = local_color_analysis['primary_color']
                result['secondary_colors'] = local_color_analysis.get('secondary_colors', [])
                result['color_context'] = local_color_analysis.get('context', 'unknown')
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing parent message: {e}")
            # Fallback to local analysis
            return self._fallback_analysis(message, context)
    
    def analyze_color_request_enhanced(self, message: str, logo_url: str = None) -> Dict:
        """Enhanced color analysis with better multi-color handling"""
        
        system_prompt = """You are an expert in color analysis for sports team merchandise. 
        Analyze the user's message to identify their color preferences with the following priorities:
        
        1. If multiple colors are mentioned, identify the PRIMARY color (usually first mentioned or preceded by priority words)
        2. Identify any SECONDARY colors mentioned
        3. Consider context clues like "mainly", "primarily", "prefer", "in" for prioritization
        4. For phrases like "X and Y colors", treat X as primary unless context suggests otherwise
        
        Available color families: red, blue, green, black, white, orange, yellow, purple, gray, pink, brown
        
        Respond in JSON format:
        {
            "recommended_color": "primary color recommendation",
            "color_family": "color family (red, blue, etc.)",
            "secondary_colors": ["list of other colors mentioned"],
            "confidence": 0.0-1.0,
            "reasoning": "explanation of why this color was chosen as primary",
            "logo_color_request": true/false,
            "alternatives": ["suggested alternative colors in same family"]
        }"""
        
        try:
            context_message = message
            if logo_url:
                context_message += f"\nLogo URL provided: {logo_url}"
                
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context_message}
                ],
                temperature=0.2,
                max_tokens=300
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Enhance with local analysis
            local_analysis = self._analyze_colors_locally(message)
            if local_analysis.get('confidence', 0) > result.get('confidence', 0):
                result['recommended_color'] = local_analysis['primary_color']
                result['secondary_colors'] = local_analysis.get('secondary_colors', [])
                result['confidence'] = local_analysis['confidence']
                result['reasoning'] = f"Local analysis (confidence: {local_analysis['confidence']:.2f})"
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing color request: {e}")
            return self._analyze_colors_locally(message)
    
    def _analyze_colors_locally(self, text: str) -> Dict:
        """Local color analysis as fallback and enhancement"""
        text_lower = text.lower()
        
        # Find all color mentions with positions
        color_matches = []
        for family, colors in self.color_families.items():
            for color in colors:
                pattern = r'\b' + re.escape(color) + r'\b'
                matches = list(re.finditer(pattern, text_lower))
                for match in matches:
                    color_matches.append({
                        'color': color,
                        'family': family,
                        'position': match.start(),
                        'end': match.end()
                    })
        
        if not color_matches:
            return {
                'primary_color': None,
                'secondary_colors': [],
                'confidence': 0.0,
                'context': 'no_colors_found'
            }
        
        # Sort by position
        color_matches.sort(key=lambda x: x['position'])
        
        # Determine primary color
        primary_color = self._determine_primary_color_local(text_lower, color_matches)
        secondary_colors = [m['color'] for m in color_matches if m['color'] != primary_color['color']]
        
        # Calculate confidence
        confidence = 0.7
        if len(color_matches) == 1:
            confidence = 0.9
        
        # Check for priority phrases
        priority_phrases = ["mainly", "primarily", "prefer", "want", "looking for"]
        for phrase in priority_phrases:
            if phrase in text_lower:
                confidence += 0.1
                break
        
        return {
            'primary_color': primary_color['color'],
            'color_family': primary_color['family'],
            'secondary_colors': secondary_colors,
            'confidence': min(1.0, confidence),
            'context': 'multiple_colors' if len(color_matches) > 1 else 'single_color'
        }
    
    def _determine_primary_color_local(self, text: str, color_matches: List[Dict]) -> Dict:
        """Determine primary color from multiple matches"""
        if len(color_matches) == 1:
            return color_matches[0]
        
        # Check for priority phrases
        priority_phrases = ["mainly", "primarily", "prefer", "want", "looking for", "in"]
        for phrase in priority_phrases:
            phrase_pos = text.find(phrase)
            if phrase_pos != -1:
                # Find closest color after priority phrase
                for color_match in color_matches:
                    if color_match['position'] > phrase_pos:
                        return color_match
        
        # For "X and Y" patterns, prioritize first color
        if " and " in text:
            return color_matches[0]
        
        # Default to first mentioned
        return color_matches[0]
    
    def _fallback_analysis(self, message: str, context: str = "") -> Dict:
        """Fallback analysis when OpenAI fails"""
        message_lower = message.lower()
        
        # Basic product type detection
        product_type = None
        if any(word in message_lower for word in ["hoodie", "sweatshirt"]):
            product_type = "hoodie"
        elif any(word in message_lower for word in ["shirt", "tee", "jersey"]):
            product_type = "shirt"
        
        # Basic color detection
        color_analysis = self._analyze_colors_locally(message)
        
        return {
            "product_specified": product_type is not None,
            "product_type": product_type,
            "sport_mentioned": None,
            "team_mentioned": None,
            "wants_logo": "logo" in message_lower,
            "primary_color": color_analysis.get('primary_color'),
            "secondary_colors": color_analysis.get('secondary_colors', []),
            "color_context": color_analysis.get('context', 'unknown'),
            "response_message": "I'd be happy to help you create custom merchandise for your team!",
            "needs_clarification": True
        }
    
    def get_logo_inspired_colors(self, logo_url: str) -> Dict:
        """Analyze logo colors for inspiration (enhanced version)"""
        
        system_prompt = """You are an expert in logo color analysis for sports merchandise. 
        Based on the logo provided, suggest primary and complementary colors that would work well 
        for team merchandise (t-shirts, hoodies, etc.).
        
        Consider:
        1. Dominant colors in the logo
        2. Colors that would make the logo pop on merchandise
        3. Traditional sports team color combinations
        4. Readability and contrast
        
        Respond in JSON format:
        {
            "dominant_colors": ["list of main colors in logo"],
            "recommended_primary": "best primary color for merchandise",
            "recommended_secondary": "best secondary/accent color",
            "alternatives": ["other good color options"],
            "contrast_colors": ["colors that make logo pop"],
            "reasoning": "explanation of color choices"
        }"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": "Please analyze this logo for color recommendations:"},
                            {"type": "image_url", "image_url": {"url": logo_url}}
                        ]
                    }
                ],
                temperature=0.3,
                max_tokens=400
            )
            
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error analyzing logo colors: {e}")
            return {
                "dominant_colors": ["unknown"],
                "recommended_primary": "black",  # Safe default
                "recommended_secondary": "white",
                "alternatives": ["navy", "red", "blue"],
                "contrast_colors": ["white", "black"],
                "reasoning": "Fallback to safe color choices due to analysis error"
            }