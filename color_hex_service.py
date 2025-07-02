#!/usr/bin/env python3

class ColorHexService:
    """Service to provide hex color codes for Printify color names"""
    
    # Curated mapping based on common Printify colors
    # These would need to be gathered from actual Printify swatches
    PRINTIFY_COLOR_HEX_MAP = {
        # Blues
        "Aqua": "#00FFFF",
        "Royal Blue": "#4169E1", 
        "Navy": "#000080",
        "Light Blue": "#ADD8E6",
        "Sky Blue": "#87CEEB",
        "Columbia Blue": "#B9D9EB",
        "Midnight Navy": "#2C3E50",
        "Cool Blue": "#0066CC",
        "Tahiti Blue": "#006994",
        
        # Reds
        "Red": "#FF0000",
        "Cardinal Red": "#C41E3A",
        "Maroon": "#800000",
        
        # Greens
        "Forest Green": "#228B22",
        "Kelly Green": "#4CBB17",
        "Military Green": "#4B5320",
        
        # Basics
        "Black": "#000000",
        "White": "#FFFFFF",
        "Solid White": "#FFFFFF",
        "Heather Grey": "#A8A8A8",
        "Light Grey": "#D3D3D3",
        "Heavy Metal": "#2C3539",
        
        # Other colors
        "Purple": "#800080",
        "Purple Rush": "#6A0DAD",
        "Gold": "#FFD700",
        "Natural": "#F5F5DC",
        "Cream": "#FFFDD0",
        "Desert Pink": "#EDC9AF"
    }
    
    @classmethod
    def get_hex_for_color(cls, color_name: str) -> str:
        """Get hex code for a Printify color name"""
        return cls.PRINTIFY_COLOR_HEX_MAP.get(color_name, "#808080")  # Default to gray
    
    @classmethod
    def get_color_with_hex(cls, color_name: str) -> dict:
        """Get color information with both name and hex"""
        return {
            "name": color_name,
            "hex": cls.get_hex_for_color(color_name)
        }
    
    @classmethod
    def get_colors_with_hex(cls, color_names: list) -> list:
        """Get list of colors with hex codes"""
        return [cls.get_color_with_hex(name) for name in color_names]

# Example usage:
if __name__ == "__main__":
    service = ColorHexService()
    
    # Test some colors
    test_colors = ["Royal Blue", "Navy", "White", "Forest Green"]
    
    print("🎨 Color Hex Mapping Test:")
    for color in test_colors:
        hex_code = service.get_hex_for_color(color)
        print(f"   {color}: {hex_code}")
    
    print(f"\n📊 Full color data:")
    color_data = service.get_colors_with_hex(test_colors)
    for color in color_data:
        print(f"   {color}")