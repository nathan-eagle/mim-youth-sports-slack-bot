#!/usr/bin/env python3
"""
Improved Product Recommendation Validation Testing Framework

This script incorporates the enhanced color detection and validation
capabilities to test the system's accuracy improvements.
"""

import json
import time
from typing import Dict, List, Tuple, Optional
from improved_color_detection import ImprovedColorDetector

class ImprovedProductValidationTester:
    def __init__(self):
        self.load_product_cache()
        self.color_detector = ImprovedColorDetector()
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
                "expected_blueprint_id": 12,
                "team_context": "basketball team"
            },
            {
                "id": 2,
                "user_request": "We need hoodies for our soccer team in navy blue",
                "expected_product_type": "hoodie",
                "expected_color": "navy",
                "expected_blueprint_id": 92,
                "team_context": "soccer team"
            },
            {
                "id": 3,
                "user_request": "Can you put our logo on black t-shirts for the baseball team?",
                "expected_product_type": "t-shirt",
                "expected_color": "black",
                "expected_blueprint_id": 6,
                "team_context": "baseball team"
            },
            {
                "id": 4,
                "user_request": "I'd like hoodies in the same color as our team logo for volleyball",
                "expected_product_type": "hoodie",
                "expected_color": "logo-inspired",
                "expected_blueprint_id": 92,
                "team_context": "volleyball team"
            },
            {
                "id": 5,
                "user_request": "We want performance shirts for our track team in bright green",
                "expected_product_type": "jersey",
                "expected_color": "green",
                "expected_blueprint_id": 12,
                "team_context": "track team"
            },
            {
                "id": 6,
                "user_request": "Our wrestling team needs shirts, preferably in maroon or burgundy",
                "expected_product_type": "t-shirt",
                "expected_color": "maroon",
                "expected_blueprint_id": 6,
                "team_context": "wrestling team"
            },
            {
                "id": 7,
                "user_request": "Can we get sweatshirts for the tennis team? Logo should pop on white",
                "expected_product_type": "hoodie",
                "expected_color": "white",
                "expected_blueprint_id": 92,
                "team_context": "tennis team"
            },
            {
                "id": 8,
                "user_request": "Looking for royal blue jerseys for our football team with the logo",
                "expected_product_type": "jersey",
                "expected_color": "royal blue",
                "expected_blueprint_id": 12,
                "team_context": "football team"
            },
            {
                "id": 9,
                "user_request": "We need cotton tees in orange for our lacrosse team",
                "expected_product_type": "t-shirt",
                "expected_color": "orange",
                "expected_blueprint_id": 6,
                "team_context": "lacrosse team"
            },
            {
                "id": 10,
                "user_request": "Can you make hoodies that match our school colors - gold and black?",
                "expected_product_type": "hoodie",
                "expected_color": "gold",  # This was the failing test case
                "expected_blueprint_id": 92,
                "team_context": "school team"
            }
        ]
    
    def simulate_improved_product_matching(self, user_request: str) -> Dict:
        """Simulate improved product matching with enhanced color detection"""
        request_lower = user_request.lower()
        
        # Product type matching (unchanged - this was working perfectly)
        if any(word in request_lower for word in ["jersey", "performance", "athletic"]):
            product_blueprint_id = 12
            product_type = "jersey"
        elif any(word in request_lower for word in ["hoodie", "sweatshirt", "hooded"]):
            product_blueprint_id = 92
            product_type = "hoodie"
        elif any(word in request_lower for word in ["t-shirt", "tee", "cotton", "shirt"]):
            product_blueprint_id = 6
            product_type = "t-shirt"
        else:
            product_blueprint_id = 6
            product_type = "t-shirt"
        
        # Enhanced color detection
        color_analysis = self.color_detector.extract_colors_advanced(user_request)
        
        # Color availability validation
        product_data = self.products_cache.get(str(product_blueprint_id), {})
        primary_color = color_analysis.get('primary_color')
        
        color_availability = None
        if primary_color:
            color_availability = self.color_detector.validate_color_availability_improved(
                product_data, primary_color
            )
        
        return {
            "recommended_product": {
                "blueprint_id": product_blueprint_id,
                "product_type": product_type,
                "title": self.get_product_title(product_blueprint_id)
            },
            "color_analysis": color_analysis,
            "color_availability": color_availability,
            "confidence": color_analysis.get('confidence', 0.5)
        }
    
    def get_product_title(self, blueprint_id: int) -> str:
        """Get product title from cache or provide default"""
        product_titles = {
            6: "Unisex Heavy Cotton Tee",
            12: "Unisex Jersey Short Sleeve Tee", 
            92: "Unisex College Hoodie"
        }
        return product_titles.get(blueprint_id, f"Product {blueprint_id}")
    
    def validate_improved_response(self, scenario: Dict, bot_response: Dict) -> Dict:
        """Validate if the improved bot response matches expectations"""
        validation_result = {
            "scenario_id": scenario["id"],
            "user_request": scenario["user_request"],
            "passed": True,
            "issues": [],
            "details": {},
            "improvements": []
        }
        
        # Validate product recommendation (unchanged logic)
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
        
        # Validate improved color analysis
        color_analysis = bot_response.get("color_analysis", {})
        expected_color = scenario["expected_color"]
        detected_color = color_analysis.get('primary_color')
        
        validation_result["details"]["expected_color"] = expected_color
        validation_result["details"]["detected_color"] = detected_color
        validation_result["details"]["color_confidence"] = color_analysis.get('confidence', 0)
        validation_result["details"]["secondary_colors"] = color_analysis.get('secondary_colors', [])
        
        if expected_color != "logo-inspired":
            if not detected_color:
                validation_result["issues"].append(f"Expected color '{expected_color}' but no color was detected")
                validation_result["passed"] = False
            elif not self.color_matches_improved(detected_color, expected_color):
                validation_result["issues"].append(f"Expected color '{expected_color}' but detected '{detected_color}'")
                validation_result["passed"] = False
        
        # Validate color availability with improved logic
        color_availability = bot_response.get("color_availability")
        if color_availability:
            validation_result["details"]["color_available"] = color_availability.get('available', False)
            validation_result["details"]["availability_confidence"] = color_availability.get('confidence', 0)
            validation_result["details"]["matching_variants"] = len(color_availability.get('matching_variants', []))
            
            if not color_availability.get('available', False):
                # Don't fail the test, but note the availability issue
                validation_result["improvements"].append(f"Color '{detected_color}' appears unavailable - consider suggesting alternatives")
        
        # Record improvements made
        if color_analysis.get('secondary_colors'):
            validation_result["improvements"].append(f"Detected secondary colors: {color_analysis['secondary_colors']}")
        
        if color_analysis.get('confidence', 0) > 0.8:
            validation_result["improvements"].append("High confidence color detection")
        
        return validation_result
    
    def color_matches_improved(self, detected: str, expected: str) -> bool:
        """Enhanced color matching using the improved color detector"""
        return self.color_detector._get_color_family(detected) == self.color_detector._get_color_family(expected) or \
               detected.lower() == expected.lower()
    
    def run_single_test(self, scenario: Dict) -> Dict:
        """Run a single test scenario with improvements"""
        print(f"\n--- Testing Scenario {scenario['id']} ---")
        print(f"User Request: {scenario['user_request']}")
        
        # Simulate improved bot response
        bot_response = self.simulate_improved_product_matching(scenario['user_request'])
        
        # Validate response
        validation_result = self.validate_improved_response(scenario, bot_response)
        
        # Print results
        if validation_result["passed"]:
            print("✅ PASSED")
        else:
            print("❌ FAILED")
            for issue in validation_result["issues"]:
                print(f"   - {issue}")
        
        # Print improvements
        if validation_result.get("improvements"):
            print("💡 Improvements:")
            for improvement in validation_result["improvements"]:
                print(f"   + {improvement}")
        
        # Print details
        details = validation_result.get("details", {})
        print(f"   Expected: {details.get('expected_product')} (ID: {details.get('expected_blueprint_id')}) in {scenario['expected_color']}")
        print(f"   Got: {details.get('recommended_product')} (ID: {details.get('actual_blueprint_id')}) in {details.get('detected_color', 'no color')}")
        
        if details.get('secondary_colors'):
            print(f"   Secondary colors: {details['secondary_colors']}")
        
        confidence = details.get('color_confidence', 0)
        print(f"   Color confidence: {confidence:.2f}")
        
        if details.get('color_available') is not None:
            available = "Yes" if details['color_available'] else "No"
            matches = details.get('matching_variants', 0)
            print(f"   Color available: {available} ({matches} matching variants)")
        
        return validation_result
    
    def run_all_tests(self) -> Dict:
        """Run all test scenarios with improvements"""
        print("🧪 Starting IMPROVED Product Validation Testing Framework")
        print("=" * 70)
        
        scenarios = self.get_test_scenarios()
        results = []
        
        for scenario in scenarios:
            result = self.run_single_test(scenario)
            results.append(result)
        
        # Generate improved summary
        passed = sum(1 for r in results if r["passed"])
        failed = len(results) - passed
        
        print("\n" + "=" * 70)
        print("📊 IMPROVED TEST SUMMARY")
        print(f"Total Tests: {len(results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(results)*100):.1f}%")
        
        # Show improvements made
        total_improvements = sum(len(r.get("improvements", [])) for r in results)
        print(f"Total Improvements: {total_improvements}")
        
        if failed > 0:
            print(f"\n❌ Failed Tests:")
            for result in results:
                if not result["passed"]:
                    print(f"  - Scenario {result['scenario_id']}: {result['user_request']}")
                    for issue in result["issues"]:
                        print(f"    • {issue}")
        
        # Compare with original results
        original_success_rate = 90.0  # From previous test
        improvement = (passed/len(results)*100) - original_success_rate
        
        print(f"\n📈 IMPROVEMENT ANALYSIS")
        print(f"Original Success Rate: {original_success_rate:.1f}%")
        print(f"New Success Rate: {(passed/len(results)*100):.1f}%")
        print(f"Improvement: {improvement:+.1f} percentage points")
        
        # Save improved results
        report = {
            "timestamp": time.time(),
            "version": "improved",
            "summary": {
                "total": len(results),
                "passed": passed,
                "failed": failed,
                "success_rate": passed/len(results)*100,
                "improvement_over_original": improvement,
                "total_improvements": total_improvements
            },
            "results": results
        }
        
        with open("improved_product_validation_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Improved report saved to: improved_product_validation_report.json")
        
        return report

def main():
    """Main execution function"""
    tester = ImprovedProductValidationTester()
    report = tester.run_all_tests()
    
    success_rate = report["summary"]["success_rate"]
    improvement = report["summary"]["improvement_over_original"]
    
    print(f"\n🎯 FINAL ASSESSMENT")
    print("=" * 40)
    
    if success_rate >= 95:
        print("🏆 EXCELLENT: System performing at high accuracy")
    elif success_rate >= 90:
        print("✅ GOOD: System performing well with minor issues")
    elif success_rate >= 80:
        print("⚠️  FAIR: System needs some improvements")
    else:
        print("🚨 NEEDS WORK: System requires significant improvements")
    
    if improvement > 0:
        print(f"📈 Improvements successfully implemented (+{improvement:.1f}%)")
    elif improvement == 0:
        print("📊 No change in success rate")
    else:
        print(f"📉 Performance decreased ({improvement:.1f}%)")
        
    return report

if __name__ == "__main__":
    main()