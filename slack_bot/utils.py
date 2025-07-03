"""
Utility functions for Slack bot
"""
import re
from typing import Optional, List


def is_asking_for_options(text: str) -> bool:
    """Check if user is asking for product options"""
    option_keywords = [
        'what do you have',
        'what products',
        'what options',
        'show me',
        'what can you',
        'what type',
        'what kind',
        'available',
        'options',
        'choices'
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in option_keywords)


def extract_requested_color(text: str) -> Optional[str]:
    """Extract color request from text"""
    # Common color names
    colors = [
        'black', 'white', 'red', 'blue', 'green', 'yellow', 'orange', 'purple',
        'pink', 'gray', 'grey', 'navy', 'maroon', 'gold', 'silver', 'brown',
        'teal', 'turquoise', 'coral', 'mint', 'olive', 'charcoal', 'heather'
    ]
    
    text_lower = text.lower()
    
    # Look for explicit color mentions
    for color in colors:
        if color in text_lower:
            return color.title()
    
    # Look for patterns like "in [color]"
    match = re.search(r'in\s+(\w+)', text_lower)
    if match:
        potential_color = match.group(1)
        if potential_color in colors:
            return potential_color.title()
    
    return None


def extract_product_types(text: str) -> List[str]:
    """Extract product types from text"""
    # Product type mappings
    product_mappings = {
        'tshirt': ['shirt', 't-shirt', 'tee', 'tshirt', 't shirt'],
        'hoodie': ['hoodie', 'hoody', 'sweatshirt', 'hooded'],
        'headwear': ['hat', 'cap', 'beanie', 'snapback'],
        'tank': ['tank', 'tank top', 'racerback', 'muscle'],
        'long_sleeve': ['long sleeve', 'longsleeve', 'long-sleeve']
    }
    
    text_lower = text.lower()
    found_products = []
    
    for product_type, keywords in product_mappings.items():
        for keyword in keywords:
            if keyword in text_lower and product_type not in found_products:
                found_products.append(product_type)
                break
    
    return found_products


def format_product_list(products: List[str]) -> str:
    """Format a list of products for display"""
    if not products:
        return ""
    elif len(products) == 1:
        return products[0]
    elif len(products) == 2:
        return f"{products[0]} and {products[1]}"
    else:
        return f"{', '.join(products[:-1])}, and {products[-1]}"


def is_affirmative(text: str) -> bool:
    """Check if text is an affirmative response"""
    affirmative_words = [
        'yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'sounds good',
        'perfect', 'great', 'lets do it', "let's do it", 'go ahead'
    ]
    
    text_lower = text.lower().strip()
    return any(word in text_lower for word in affirmative_words)


def is_negative(text: str) -> bool:
    """Check if text is a negative response"""
    negative_words = [
        'no', 'nope', 'not', "don't", 'cancel', 'stop', 'nevermind',
        'never mind', 'forget it'
    ]
    
    text_lower = text.lower().strip()
    return any(word in text_lower for word in negative_words)