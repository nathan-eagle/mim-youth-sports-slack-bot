#!/usr/bin/env python3
"""
Product Recommendation and Mockup Validation Testing Framework

This script tests the accuracy of product recommendations and mockup generation
by simulating realistic user requests and validating the system's responses.
"""

import json
import time
import requests
from typing import Dict, List, Tuple, Optional
from openai_service import OpenAIService
from product_service import ProductService
from printify_service import PrintifyService
from logo_processor import LogoProcessor
from conversation_manager import ConversationManager

class ProductValidationTester:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.product_service = ProductService()
        self.printify_service = PrintifyService()
        self.logo_processor = LogoProcessor()
        self.conversation_manager = ConversationManager()
        self.test_results = []
        
    def get_test_scenarios(self) -> List[Dict]:
        """Define 10 realistic user request scenarios for testing"""
        return [
            {
                "id": 1,
                "user_request": "I want our logo on a bright red jersey t-shirt for my basketball team",
                "expected_product": "Unisex Jersey Short Sleeve Tee",
                "expected_color": "red",
                "logo_url": "https://example.com/basketball-logo.png",
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
                "expected_product": "Unisex College Hoodie",
                "expected_color": "navy",
                "logo_url": "https://example.com/soccer-logo.png",
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
                "expected_product": "Unisex Heavy Cotton Tee",
                "expected_color": "black",
                "logo_url": "https://example.com/baseball-logo.png",
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
                "expected_product": "Unisex College Hoodie",
                "expected_color": "logo-inspired",
                "logo_url": "https://example.com/volleyball-logo-purple.png",
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
                "expected_product": "Unisex Jersey Short Sleeve Tee",
                "expected_color": "green",
                "logo_url": "https://example.com/track-logo.png",
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
                "expected_product": "Unisex Heavy Cotton Tee",
                "expected_color": "maroon",
                "logo_url": "https://example.com/wrestling-logo.png",
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
                "expected_product": "Unisex College Hoodie",
                "expected_color": "white",
                "logo_url": "https://example.com/tennis-logo.png",
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
                "expected_product": "Unisex Jersey Short Sleeve Tee",
                "expected_color": "royal blue",
                "logo_url": "https://example.com/football-logo.png",
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
                "expected_product": "Unisex Heavy Cotton Tee",
                "expected_color": "orange",
                "logo_url": "https://example.com/lacrosse-logo.png",
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
                "expected_product": "Unisex College Hoodie",
                "expected_color": "gold",
                "logo_url": "https://example.com/school-logo.png",
                "team_context": "school team",
                "validation_criteria": {
                    "product_type": "hoodie",
                    "color_family": "yellow",
                    "sport_appropriate": True
                }
            }
        ]
    
    def simulate_bot_response(self, scenario: Dict) -> Dict:
        """Simulate the bot's response to a user request"""
        try:
            # Create a mock conversation state
            conversation_id = f"test_{scenario['id']}"
            
            # Analyze the user request using OpenAI
            analysis = self.openai_service.analyze_parent_message(
                scenario['user_request'],
                scenario['team_context']
            )
            
            # Find the recommended product
            product_recommendation = self.product_service.find_product_by_intent_ai(
                scenario['user_request']
            )
            
            # Analyze color request
            color_analysis = self.openai_service.analyze_color_request(
                scenario['user_request'],
                scenario['logo_url']
            )
            
            # Get logo-inspired colors if applicable
            logo_colors = None
            if "same color" in scenario['user_request'].lower() or "logo" in scenario['user_request'].lower():
                logo_colors = self.openai_service.get_logo_inspired_colors(
                    scenario['logo_url']
                )
            
            return {
                "conversation_id": conversation_id,
                "analysis": analysis,
                "product_recommendation": product_recommendation,
                "color_analysis": color_analysis,
                "logo_colors": logo_colors,
                "success": True
            }
            
        except Exception as e:
            return {
                "conversation_id": f"test_{scenario['id']}",
                "error": str(e),
                "success": False
            }
    
    def validate_response(self, scenario: Dict, bot_response: Dict) -> Dict:
        """Validate if the bot's response matches expectations"""
        validation_result = {
            "scenario_id": scenario["id"],
            "user_request": scenario["user_request"],
            "passed": True,
            "issues": [],
            "details": {}
        }
        
        if not bot_response["success"]:
            validation_result["passed"] = False
            validation_result["issues"].append(f"Bot response failed: {bot_response.get('error', 'Unknown error')}")
            return validation_result
        
        # Validate product recommendation
        if bot_response.get("product_recommendation"):
            recommended_product = bot_response["product_recommendation"]
            validation_result["details"]["recommended_product"] = recommended_product
            
            # Check if the recommended product type matches expectation
            expected_product = scenario["expected_product"].lower()
            if "jersey" in expected_product and recommended_product.get("blueprint_id") != 12:
                validation_result["issues"].append("Expected jersey t-shirt but got different product")
                validation_result["passed"] = False
            elif "hoodie" in expected_product and recommended_product.get("blueprint_id") != 92:
                validation_result["issues"].append("Expected hoodie but got different product")
                validation_result["passed"] = False
            elif "heavy cotton" in expected_product and recommended_product.get("blueprint_id") != 6:
                validation_result["issues"].append("Expected heavy cotton tee but got different product")
                validation_result["passed"] = False
        else:
            validation_result["issues"].append("No product recommendation received")
            validation_result["passed"] = False
        
        # Validate color analysis
        if bot_response.get("color_analysis"):
            color_analysis = bot_response["color_analysis"]
            validation_result["details"]["color_analysis"] = color_analysis
            
            expected_color = scenario["expected_color"].lower()
            recommended_color = color_analysis.get("recommended_color", "").lower()
            
            # Check color family matching
            color_families = {
                "red": ["red", "maroon", "burgundy", "crimson"],
                "blue": ["blue", "navy", "royal blue", "royal"],
                "green": ["green", "forest", "lime"],
                "black": ["black"],
                "white": ["white"],
                "orange": ["orange"],
                "yellow": ["gold", "yellow"]
            }
            
            if expected_color != "logo-inspired":
                expected_family = None
                for family, colors in color_families.items():
                    if expected_color in colors:
                        expected_family = family
                        break
                
                if expected_family:
                    color_match_found = any(color in recommended_color for color in color_families[expected_family])
                    if not color_match_found:
                        validation_result["issues"].append(f"Expected {expected_color} color but got {recommended_color}")
                        validation_result["passed"] = False
        else:
            validation_result["issues"].append("No color analysis received")
            validation_result["passed"] = False
        
        # Validate logo color analysis if applicable
        if scenario["expected_color"] == "logo-inspired" and bot_response.get("logo_colors"):
            logo_colors = bot_response["logo_colors"]
            validation_result["details"]["logo_colors"] = logo_colors
            
            if not logo_colors.get("colors"):
                validation_result["issues"].append("Expected logo color analysis but got no colors")
                validation_result["passed"] = False
        
        return validation_result
    
    def run_single_test(self, scenario: Dict) -> Dict:
        """Run a single test scenario"""
        print(f"\n--- Testing Scenario {scenario['id']} ---")
        print(f"User Request: {scenario['user_request']}")
        
        # Simulate bot response
        bot_response = self.simulate_bot_response(scenario)
        
        # Validate response
        validation_result = self.validate_response(scenario, bot_response)
        
        # Print results
        if validation_result["passed"]:
            print("✅ PASSED")
        else:
            print("❌ FAILED")
            for issue in validation_result["issues"]:
                print(f"   - {issue}")
        
        if validation_result.get("details"):
            print(f"   Details: {json.dumps(validation_result['details'], indent=2)}")
        
        return validation_result
    
    def run_all_tests(self) -> Dict:
        """Run all test scenarios and generate a summary report"""
        print("🧪 Starting Product Validation Testing Framework")
        print("=" * 60)
        
        scenarios = self.get_test_scenarios()
        results = []
        
        for scenario in scenarios:
            result = self.run_single_test(scenario)
            results.append(result)
            time.sleep(1)  # Avoid rate limiting
        
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
        
        # Save detailed results
        report = {
            "timestamp": time.time(),
            "summary": {
                "total": len(results),
                "passed": passed,
                "failed": failed,
                "success_rate": passed/len(results)*100
            },
            "results": results
        }
        
        with open("product_validation_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: product_validation_report.json")
        
        return report

def main():
    """Main execution function"""
    tester = ProductValidationTester()
    report = tester.run_all_tests()
    
    # If there are failures, suggest improvements
    if report["summary"]["failed"] > 0:
        print("\n🔧 IMPROVEMENT SUGGESTIONS")
        print("Based on the test failures, consider:")
        print("1. Improving product keyword matching in OpenAI prompts")
        print("2. Enhancing color analysis accuracy")
        print("3. Adding more robust fallback logic")
        print("4. Expanding the product catalog for better matching")
        
    return report

if __name__ == "__main__":
    main()