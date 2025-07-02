#!/usr/bin/env python3
"""
Improved Color Detection Module

This module provides enhanced color detection and validation capabilities
for the product recommendation system, addressing the issues identified
in the validation testing.
"""

import re
from typing import Dict, List, Tuple, Optional, Set

class ImprovedColorDetector:
    def __init__(self):
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
        
        # Common color phrases and their priorities
        self.color_priority_phrases = [
            "mainly", "primarily", "mostly", "predominately", 
            "prefer", "want", "looking for", "in"
        ]
    
    def extract_colors_advanced(self, text: str) -> Dict:
        """
        Advanced color extraction that handles multiple colors and context
        """
        text_lower = text.lower()
        
        # Find all color mentions with their positions
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
        
        # Sort by position to maintain order
        color_matches.sort(key=lambda x: x['position'])
        
        if not color_matches:
            return {
                'primary_color': None,
                'secondary_colors': [],
                'all_colors': [],
                'confidence': 0.0,
                'context': 'no_colors_found'
            }
        
        # Determine primary color based on context
        primary_color = self._determine_primary_color(text_lower, color_matches)
        
        # Extract secondary colors
        secondary_colors = [
            match['color'] for match in color_matches 
            if match['color'] != primary_color['color']
        ]
        
        # Calculate confidence based on context
        confidence = self._calculate_color_confidence(text_lower, color_matches)
        
        return {
            'primary_color': primary_color['color'],
            'primary_family': primary_color['family'],
            'secondary_colors': secondary_colors,
            'all_colors': [match['color'] for match in color_matches],
            'confidence': confidence,
            'context': self._analyze_color_context(text_lower, color_matches)
        }
    
    def _determine_primary_color(self, text: str, color_matches: List[Dict]) -> Dict:
        """
        Determine which color should be considered primary based on context
        """
        if len(color_matches) == 1:
            return color_matches[0]
        
        # Check for priority phrases that indicate primary color
        for phrase in self.color_priority_phrases:
            phrase_pos = text.find(phrase)
            if phrase_pos != -1:
                # Find the closest color after the priority phrase
                closest_color = None
                min_distance = float('inf')
                
                for color_match in color_matches:
                    if color_match['position'] > phrase_pos:
                        distance = color_match['position'] - phrase_pos
                        if distance < min_distance:
                            min_distance = distance
                            closest_color = color_match
                
                if closest_color:
                    return closest_color
        
        # Special handling for common patterns
        if "and" in text:
            # For "X and Y", prioritize the first color mentioned
            return color_matches[0]
        
        # Default to first mentioned color
        return color_matches[0]
    
    def _calculate_color_confidence(self, text: str, color_matches: List[Dict]) -> float:
        """
        Calculate confidence score for color detection
        """
        base_confidence = 0.7
        
        # Boost confidence for single color mentions
        if len(color_matches) == 1:
            base_confidence += 0.2
        
        # Boost confidence for priority phrases
        for phrase in self.color_priority_phrases:
            if phrase in text:
                base_confidence += 0.1
                break
        
        # Reduce confidence for multiple colors without clear priority
        if len(color_matches) > 2:
            base_confidence -= 0.1
        
        return min(1.0, base_confidence)
    
    def _analyze_color_context(self, text: str, color_matches: List[Dict]) -> str:
        """
        Analyze the context of color mentions
        """
        if len(color_matches) == 1:
            return "single_color"
        elif len(color_matches) == 2:
            if "and" in text:
                return "dual_colors"
            else:
                return "color_alternatives"
        elif len(color_matches) > 2:
            return "multiple_colors"
        else:
            return "no_colors"
    
    def validate_color_availability_improved(self, product_data: Dict, color: str) -> Dict:
        """
        Improved color availability validation with better variant parsing
        """
        if not product_data or 'variants' not in product_data:
            return {
                'available': False,
                'confidence': 0.0,
                'matching_variants': [],
                'reason': 'no_variant_data'
            }
        
        variants = product_data['variants']
        matching_variants = []
        
        # Enhanced color matching in variant titles
        color_family = self._get_color_family(color)
        
        for variant in variants:
            variant_title = variant.get('title', '').lower()
            
            # Direct color match
            if color.lower() in variant_title:
                matching_variants.append({
                    'id': variant.get('id'),
                    'title': variant.get('title'),
                    'match_type': 'direct'
                })
                continue
            
            # Family match (e.g., "maroon" matches "red" family)
            if color_family:
                family_colors = self.color_families[color_family]
                for family_color in family_colors:
                    if family_color in variant_title:
                        matching_variants.append({
                            'id': variant.get('id'),
                            'title': variant.get('title'),
                            'match_type': 'family',
                            'matched_color': family_color
                        })
                        break
        
        # Calculate availability confidence
        total_variants = len(variants)
        matching_count = len(matching_variants)
        
        if matching_count > 0:
            confidence = min(1.0, matching_count / max(1, total_variants) * 3)  # Scale confidence
            return {
                'available': True,
                'confidence': confidence,
                'matching_variants': matching_variants[:5],  # Limit to first 5 matches
                'reason': f'found_{matching_count}_matches',
                'total_variants': total_variants
            }
        else:
            return {
                'available': False,
                'confidence': 0.0,
                'matching_variants': [],
                'reason': 'no_color_matches_found',
                'total_variants': total_variants,
                'sample_variants': [v.get('title', '') for v in variants[:3]]  # Show sample for debugging
            }
    
    def _get_color_family(self, color: str) -> Optional[str]:
        """
        Get the color family for a given color
        """
        color_lower = color.lower()
        for family, colors in self.color_families.items():
            if color_lower in colors:
                return family
        return None
    
    def suggest_alternative_colors(self, product_data: Dict, requested_color: str) -> List[Dict]:
        """
        Suggest alternative colors if requested color is not available
        """
        if not product_data or 'variants' not in product_data:
            return []
        
        # Extract all available colors from variants
        available_colors = set()
        variants = product_data['variants']
        
        for variant in variants:
            variant_title = variant.get('title', '').lower()
            
            # Extract color words from variant titles
            for family, colors in self.color_families.items():
                for color in colors:
                    if color in variant_title:
                        available_colors.add(color)
        
        # Suggest colors from same family first
        requested_family = self._get_color_family(requested_color)
        suggestions = []
        
        if requested_family:
            family_colors = [c for c in available_colors if self._get_color_family(c) == requested_family]
            suggestions.extend([{'color': c, 'reason': 'same_family'} for c in family_colors])
        
        # Add popular colors
        popular_colors = ['black', 'white', 'navy', 'red', 'blue']
        for color in popular_colors:
            if color in available_colors and color not in [s['color'] for s in suggestions]:
                suggestions.append({'color': color, 'reason': 'popular_choice'})
        
        return suggestions[:5]  # Limit to 5 suggestions

# Test the improved color detection
def test_improved_color_detection():
    """
    Test the improved color detection with the problematic scenarios
    """
    detector = ImprovedColorDetector()
    
    test_cases = [
        "Can you make hoodies that match our school colors - gold and black?",
        "We want shirts in red or blue for the team",
        "Looking for mainly navy with white accents",
        "I prefer bright green jerseys",
        "Team colors are maroon and gold - can we get hoodies?"
    ]
    
    print("🧪 Testing Improved Color Detection")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case}")
        result = detector.extract_colors_advanced(test_case)
        
        print(f"  Primary: {result['primary_color']} ({result['primary_family']})")
        print(f"  Secondary: {result['secondary_colors']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Context: {result['context']}")

if __name__ == "__main__":
    test_improved_color_detection()