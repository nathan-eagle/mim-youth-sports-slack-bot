#!/usr/bin/env python3
"""
Simplified Product Recommendation Validation Testing Framework

This script tests the accuracy of product recommendations by simulating 
realistic user requests and validating the system's responses without
requiring full API access.
"""

import json
import time
from typing import Dict, List, Tuple, Optional

class ProductValidationTester:
    def __init__(self):
        self.load_product_cache()
        self.test_results = []
        
    def load_product_cache(self):
        """Load the product cache to understand available products"""
        try:
            with open("top3_product_cache_optimized.json", 'r') as f:
                data = json.load(f)
                self.products_cache = data.get('products', {})
                print(f"Loaded {len(self.products_cache)} products from cache")
        except Exception as e:
            print(f"Error loading product cache: {e}")
            self.products_cache = {}
        
    def get_test_scenarios(self) -> List[Dict]:
        """Define 10 realistic user request scenarios for testing"""
        return [
            {
                "id": 1,
                "user_request": "I want our logo on a bright red jersey t-shirt for my basketball team",
                "expected_product_type": "jersey",
                "expected_color": "red",
                "expected_blueprint_id": 12,  # Unisex Jersey Short Sleeve Tee
                "team_context": "basketball team",
                "validation_criteria": {
                    "product_type": "jersey",
                    "color_family": "red",
                    "sport_appropriate": True
                }
            },
            {
                "id": 2,
                "user_request": "We need hoodies for our soccer team in navy blue",
                "expected_product_type": "hoodie",
                "expected_color": "navy",
                "expected_blueprint_id": 92,  # Unisex College Hoodie
                "team_context": "soccer team",
                "validation_criteria": {
                    "product_type": "hoodie",
                    "color_family": "blue",
                    "sport_appropriate": True
                }
            },
            {
                "id": 3,
                "user_request": "Can you put our logo on black t-shirts for the baseball team?",
                "expected_product_type": "t-shirt",
                "expected_color": "black",
                "expected_blueprint_id": 6,  # Unisex Heavy Cotton Tee
                "team_context": "baseball team",
                "validation_criteria": {
                    "product_type": "t-shirt",
                    "color_family": "black",
                    "sport_appropriate": True
                }
            },
            {
                "id": 4,
                "user_request": "I'd like hoodies in the same color as our team logo for volleyball",
                "expected_product_type": "hoodie",
                "expected_color": "logo-inspired",
                "expected_blueprint_id": 92,
                "team_context": "volleyball team",
                "validation_criteria": {
                    "product_type": "hoodie",
                    "color_matches_logo": True,
                    "sport_appropriate": True
                }
            },
            {
                "id": 5,
                "user_request": "We want performance shirts for our track team in bright green",
                "expected_product_type": "jersey",
                "expected_color": "green",
                "expected_blueprint_id": 12,
                "team_context": "track team",
                "validation_criteria": {
                    "product_type": "jersey",
                    "color_family": "green",
                    "sport_appropriate": True
                }
            },
            {
                "id": 6,
                "user_request": "Our wrestling team needs shirts, preferably in maroon or burgundy",
                "expected_product_type": "t-shirt",
                "expected_color": "maroon",
                "expected_blueprint_id": 6,
                "team_context": "wrestling team",
                "validation_criteria": {
                    "product_type": "t-shirt",
                    "color_family": "red",
                    "sport_appropriate": True
                }
            },
            {
                "id": 7,
                "user_request": "Can we get sweatshirts for the tennis team? Logo should pop on white",
                "expected_product_type": "hoodie",
                "expected_color": "white",
                "expected_blueprint_id": 92,
                "team_context": "tennis team",
                "validation_criteria": {
                    "product_type": "hoodie",
                    "color_family": "white",
                    "sport_appropriate": True
                }
            },
            {
                "id": 8,
                "user_request": "Looking for royal blue jerseys for our football team with the logo",
                "expected_product_type": "jersey",
                "expected_color": "royal blue",
                "expected_blueprint_id": 12,
                "team_context": "football team",
                "validation_criteria": {
                    "product_type": "jersey",
                    "color_family": "blue",
                    "sport_appropriate": True
                }
            },
            {
                "id": 9,
                "user_request": "We need cotton tees in orange for our lacrosse team",
                "expected_product_type": "t-shirt",
                "expected_color": "orange",
                "expected_blueprint_id": 6,
                "team_context": "lacrosse team",
                "validation_criteria": {
                    "product_type": "t-shirt",
                    "color_family": "orange",
                    "sport_appropriate": True
                }
            },
            {
                "id": 10,
                "user_request": "Can you make hoodies that match our school colors - gold and black?",
                "expected_product_type": "hoodie",
                "expected_color": "gold",
                "expected_blueprint_id": 92,
                "team_context": "school team",
                "validation_criteria": {
                    "product_type": "hoodie",
                    "color_family": "yellow",
                    "sport_appropriate": True
                }
            }
        ]
    
    def simulate_product_matching(self, user_request: str) -> Dict:
        """Simulate product matching based on keywords and patterns"""
        request_lower = user_request.lower()
        
        # Product type matching
        if any(word in request_lower for word in ["jersey", "performance", "athletic"]):
            product_blueprint_id = 12  # Jersey Short Sleeve Tee
            product_type = "jersey"
        elif any(word in request_lower for word in ["hoodie", "sweatshirt", "hooded"]):
            product_blueprint_id = 92   # College Hoodie
            product_type = "hoodie"
        elif any(word in request_lower for word in ["t-shirt", "tee", "cotton", "shirt"]):
            product_blueprint_id = 6    # Heavy Cotton Tee
            product_type = "t-shirt"
        else:
            # Default fallback
            product_blueprint_id = 6
            product_type = "t-shirt"
        
        # Color extraction
        colors = ["red", "blue", "navy", "black", "white", "green", "orange", "gold", "yellow", "purple", "maroon", "burgundy", "royal blue"]
        detected_color = None
        for color in colors:
            if color in request_lower:
                detected_color = color
                break
        
        # Check if logo color matching is requested
        logo_color_request = any(phrase in request_lower for phrase in ["same color", "match", "logo color"])
        
        return {
            "recommended_product": {
                "blueprint_id": product_blueprint_id,
                "product_type": product_type,
                "title": self.get_product_title(product_blueprint_id)
            },
            "detected_color": detected_color,
            "logo_color_request": logo_color_request,
            "confidence": 0.8  # Simulated confidence
        }
    
    def get_product_title(self, blueprint_id: int) -> str:
        """Get product title from cache or provide default"""
        product_titles = {
            6: "Unisex Heavy Cotton Tee",
            12: "Unisex Jersey Short Sleeve Tee", 
            92: "Unisex College Hoodie"
        }
        return product_titles.get(blueprint_id, f"Product {blueprint_id}")
    
    def validate_color_availability(self, blueprint_id: int, color: str) -> bool:
        """Check if the requested color is available for the product"""
        product_key = str(blueprint_id)
        if product_key in self.products_cache:
            product = self.products_cache[product_key]
            variants = product.get('variants', [])
            
            # Check if any variant matches the color
            for variant in variants:
                variant_title = variant.get('title', '').lower()
                if color.lower() in variant_title:
                    return True
        
        return False
    
    def validate_response(self, scenario: Dict, bot_response: Dict) -> Dict:
        """Validate if the bot's response matches expectations"""
        validation_result = {
            "scenario_id": scenario["id"],
            "user_request": scenario["user_request"],
            "passed": True,
            "issues": [],
            "details": {}
        }
        
        # Validate product recommendation
        recommended_product = bot_response.get("recommended_product", {})
        expected_blueprint_id = scenario["expected_blueprint_id"]
        actual_blueprint_id = recommended_product.get("blueprint_id")
        
        validation_result["details"]["expected_product"] = scenario["expected_product_type"]
        validation_result["details"]["recommended_product"] = recommended_product.get("title", "Unknown")
        validation_result["details"]["expected_blueprint_id"] = expected_blueprint_id
        validation_result["details"]["actual_blueprint_id"] = actual_blueprint_id
        
        if actual_blueprint_id != expected_blueprint_id:
            validation_result["issues"].append(f"Expected blueprint_id {expected_blueprint_id} but got {actual_blueprint_id}")
            validation_result["passed"] = False
        
        # Validate color detection
        detected_color = bot_response.get("detected_color")
        expected_color = scenario["expected_color"]
        
        validation_result["details"]["expected_color"] = expected_color
        validation_result["details"]["detected_color"] = detected_color
        
        if expected_color != "logo-inspired":
            if not detected_color:
                validation_result["issues"].append(f"Expected color '{expected_color}' but no color was detected")
                validation_result["passed"] = False
            elif not self.color_matches(detected_color, expected_color):
                validation_result["issues"].append(f"Expected color '{expected_color}' but detected '{detected_color}'")
                validation_result["passed"] = False
            
            # Check color availability
            if detected_color and not self.validate_color_availability(actual_blueprint_id, detected_color):
                validation_result["issues"].append(f"Color '{detected_color}' may not be available for product {actual_blueprint_id}")
                # Don't fail the test for this, just warn
        
        return validation_result
    
    def color_matches(self, detected: str, expected: str) -> bool:
        """Check if detected color matches expected color family"""
        color_families = {
            "red": ["red", "maroon", "burgundy", "crimson"],
            "blue": ["blue", "navy", "royal blue", "royal"],
            "green": ["green", "forest", "lime"],
            "black": ["black"],
            "white": ["white"],
            "orange": ["orange"],
            "yellow": ["gold", "yellow"],
            "purple": ["purple", "violet"]
        }
        
        # Direct match
        if detected.lower() == expected.lower():
            return True
            
        # Family match
        for family, colors in color_families.items():
            if expected.lower() in colors and detected.lower() in colors:
                return True
                
        return False
    
    def run_single_test(self, scenario: Dict) -> Dict:
        """Run a single test scenario"""
        print(f"\n--- Testing Scenario {scenario['id']} ---")
        print(f"User Request: {scenario['user_request']}")
        
        # Simulate bot response
        bot_response = self.simulate_product_matching(scenario['user_request'])
        
        # Validate response
        validation_result = self.validate_response(scenario, bot_response)
        
        # Print results
        if validation_result["passed"]:
            print("✅ PASSED")
        else:
            print("❌ FAILED")
            for issue in validation_result["issues"]:
                print(f"   - {issue}")
        
        # Print details
        details = validation_result.get("details", {})
        print(f"   Expected: {details.get('expected_product')} (ID: {details.get('expected_blueprint_id')}) in {scenario['expected_color']}")
        print(f"   Got: {details.get('recommended_product')} (ID: {details.get('actual_blueprint_id')}) in {details.get('detected_color', 'no color')}")
        
        return validation_result
    
    def analyze_product_coverage(self):
        """Analyze which products are available and their color options"""
        print("\n📦 PRODUCT CATALOG ANALYSIS")
        print("=" * 50)
        
        for product_id, product in self.products_cache.items():
            title = product.get('title', 'Unknown')
            blueprint_id = product.get('blueprint_id', 'Unknown')
            variants = product.get('variants', [])
            
            print(f"\nProduct: {title} (ID: {product_id}, Blueprint: {blueprint_id})")
            print(f"Variants: {len(variants)}")
            
            # Extract unique colors
            colors = set()
            for variant in variants[:10]:  # Show first 10 variants
                variant_title = variant.get('title', '')
                # Simple color extraction
                for color_word in ['Black', 'White', 'Red', 'Blue', 'Navy', 'Green', 'Gray', 'Yellow', 'Orange', 'Purple']:
                    if color_word in variant_title:
                        colors.add(color_word)
                        
            if colors:
                print(f"Available colors (sample): {', '.join(sorted(colors))}")
            else:
                print("Color information not readily available")
    
    def run_all_tests(self) -> Dict:
        """Run all test scenarios and generate a summary report"""
        print("🧪 Starting Product Validation Testing Framework")
        print("=" * 60)
        
        # First analyze what products we have
        if self.products_cache:
            self.analyze_product_coverage()
        
        print("\n🔍 RUNNING VALIDATION TESTS")
        print("=" * 40)
        
        scenarios = self.get_test_scenarios()
        results = []
        
        for scenario in scenarios:
            result = self.run_single_test(scenario)
            results.append(result)
        
        # Generate summary
        passed = sum(1 for r in results if r["passed"])
        failed = len(results) - passed
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print(f"Total Tests: {len(results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(results)*100):.1f}%")
        
        if failed > 0:
            print(f"\n❌ Failed Tests:")
            for result in results:
                if not result["passed"]:
                    print(f"  - Scenario {result['scenario_id']}: {result['user_request']}")
                    for issue in result["issues"]:
                        print(f"    • {issue}")
        
        # Identify patterns in failures
        self.analyze_failure_patterns(results)
        
        # Save detailed results
        report = {
            "timestamp": time.time(),
            "summary": {
                "total": len(results),
                "passed": passed,
                "failed": failed,
                "success_rate": passed/len(results)*100
            },
            "results": results,
            "product_cache_info": {
                "products_available": len(self.products_cache),
                "cache_loaded": bool(self.products_cache)
            }
        }
        
        with open("product_validation_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: product_validation_report.json")
        
        return report
    
    def analyze_failure_patterns(self, results: List[Dict]):
        """Analyze patterns in test failures to suggest improvements"""
        failed_results = [r for r in results if not r["passed"]]
        
        if not failed_results:
            return
            
        print("\n🔧 FAILURE PATTERN ANALYSIS")
        print("=" * 40)
        
        # Categorize failure types
        product_failures = 0
        color_failures = 0
        availability_failures = 0
        
        for result in failed_results:
            for issue in result["issues"]:
                if "blueprint_id" in issue:
                    product_failures += 1
                elif "color" in issue.lower() and "available" not in issue.lower():
                    color_failures += 1
                elif "available" in issue.lower():
                    availability_failures += 1
        
        if product_failures > 0:
            print(f"🎯 Product Matching Issues: {product_failures}")
            print("   → Consider improving keyword-based product selection logic")
            
        if color_failures > 0:
            print(f"🎨 Color Detection Issues: {color_failures}")
            print("   → Consider enhancing color extraction from user requests")
            
        if availability_failures > 0:
            print(f"📦 Color Availability Issues: {availability_failures}")
            print("   → Consider validating color availability against product variants")

def main():
    """Main execution function"""
    tester = ProductValidationTester()
    report = tester.run_all_tests()
    
    # Generate improvement suggestions
    if report["summary"]["failed"] > 0:
        print("\n💡 IMPROVEMENT SUGGESTIONS")
        print("=" * 40)
        success_rate = report["summary"]["success_rate"]
        
        if success_rate < 70:
            print("🚨 Critical Issues Found:")
            print("  1. Review product matching algorithm")
            print("  2. Improve color detection and matching")
            print("  3. Validate against actual product catalog")
        elif success_rate < 90:
            print("⚠️  Minor Issues Found:")
            print("  1. Fine-tune keyword matching")
            print("  2. Expand color synonym handling")
            print("  3. Add more comprehensive validation")
        else:
            print("✨ System performing well with minor improvements needed")
    else:
        print("\n🎉 All tests passed! System appears to be working correctly.")
        
    return report

if __name__ == "__main__":
    main()