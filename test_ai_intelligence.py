#!/usr/bin/env python3
"""
Comprehensive AI Intelligence Testing Suite
Tests the AI's decision making for product selection, color matching, and mockup quality
"""

import os
import json
import time
import logging
import requests
import openai
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Import our services
from services.product_selector import product_selector
from services.product_service import product_service
from openai_service import openai_service
from ai_color_service import ai_color_service
from printify_service import printify_service
from database_service import database_service

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AIIntelligenceTest:
    """Test suite for AI decision making and mockup quality"""
    
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        
        # Test logos for different scenarios
        self.test_logos = {
            'soccer_logo': 'https://static.wixstatic.com/media/d072b4_a933c375e992435ea9f972afc685cff9~mv2.png',
            'basketball_logo': 'https://static.wixstatic.com/media/d072b4_a933c375e992435ea9f972afc685cff9~mv2.png',
            'baseball_logo': 'https://static.wixstatic.com/media/d072b4_a933c375e992435ea9f972afc685cff9~mv2.png'
        }
        
        # Test scenarios simulating real parent requests
        self.test_scenarios = [
            {
                'name': 'Soccer Mom - Basic Request',
                'request': "I need shirts for my daughter's soccer team",
                'expected_categories': ['tshirt'],
                'sport_context': 'soccer',
                'age_group': 'youth'
            },
            {
                'name': 'Basketball Dad - Multiple Products',
                'request': "We need jerseys and hoodies for the basketball team",
                'expected_categories': ['tshirt', 'hoodie'],
                'sport_context': 'basketball',
                'age_group': 'youth'
            },
            {
                'name': 'Baseball Coach - Specific Items',
                'request': "Looking for caps and practice shirts for little league",
                'expected_categories': ['headwear', 'tshirt'],
                'sport_context': 'baseball',
                'age_group': 'kids'
            },
            {
                'name': 'Volleyball Parent - Seasonal Request',
                'request': "Need tank tops for summer volleyball and hoodies for cooler games",
                'expected_categories': ['tank', 'hoodie'],
                'sport_context': 'volleyball',
                'age_group': 'youth'
            },
            {
                'name': 'Tennis Parent - Ambiguous Request',
                'request': "My son needs gear for tennis tournaments",
                'expected_categories': ['tshirt'],  # AI should infer appropriate products
                'sport_context': 'tennis',
                'age_group': 'youth'
            }
        ]
    
    def run_all_tests(self):
        """Run comprehensive AI intelligence tests"""
        print("🧠 STARTING AI INTELLIGENCE TESTING SUITE")
        print("=" * 60)
        
        # Test 1: Product Selection Intelligence
        self.test_product_selection_ai()
        
        # Test 2: Color Selection Intelligence
        self.test_color_selection_ai()
        
        # Test 3: End-to-End Mockup Generation
        self.test_mockup_generation()
        
        # Test 4: Mockup Quality Analysis
        self.test_mockup_quality_analysis()
        
        # Generate final report
        self.generate_test_report()
    
    def test_product_selection_ai(self):
        """Test AI product selection for various scenarios"""
        print("\n🎯 TESTING AI PRODUCT SELECTION")
        print("-" * 40)
        
        for scenario in self.test_scenarios:
            print(f"\n📝 Testing: {scenario['name']}")
            print(f"Request: \"{scenario['request']}\"")
            
            try:
                # Simulate conversation context
                conversation_context = {
                    'sport_context': scenario['sport_context'],
                    'age_group': scenario['age_group']
                }
                
                # Test AI product selection
                selection_result = product_selector.select_products_from_conversation(
                    scenario['request'], 
                    conversation_context
                )
                
                if selection_result['success']:
                    selected_categories = selection_result.get('categories', [])
                    selected_products = selection_result.get('selected_products', [])
                    alternatives = selection_result.get('alternatives', {})
                    
                    print(f"✅ AI Selected Categories: {selected_categories}")
                    print(f"✅ AI Selected Products: {[p['title'] for p in selected_products]}")
                    
                    # Check if AI made reasonable selections
                    reasonable_selection = self._evaluate_product_selection(
                        scenario, selected_categories, selected_products
                    )
                    
                    if reasonable_selection:
                        print("✅ AI selection is reasonable for the request")
                        
                        # Test complementary suggestions
                        complementary = product_selector.suggest_complementary_products(selected_categories)
                        if complementary:
                            print(f"✅ AI suggested complementary: {[p['title'] for p in complementary]}")
                        
                        self.test_results.append({
                            'test': f"Product Selection - {scenario['name']}",
                            'status': 'PASS',
                            'ai_selection': selected_categories,
                            'ai_reasoning': 'Appropriate products for sport and context'
                        })
                    else:
                        print("❌ AI selection seems inappropriate")
                        self.failed_tests.append({
                            'test': f"Product Selection - {scenario['name']}",
                            'issue': 'Inappropriate product selection',
                            'selected': selected_categories,
                            'expected': scenario['expected_categories']
                        })
                else:
                    print(f"❌ AI failed to understand request: {selection_result.get('error')}")
                    self.failed_tests.append({
                        'test': f"Product Selection - {scenario['name']}",
                        'issue': 'AI failed to understand request',
                        'error': selection_result.get('error')
                    })
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Error testing {scenario['name']}: {e}")
                self.failed_tests.append({
                    'test': f"Product Selection - {scenario['name']}",
                    'issue': 'Exception occurred',
                    'error': str(e)
                })
    
    def test_color_selection_ai(self):
        """Test AI color selection and matching"""
        print("\n🎨 TESTING AI COLOR SELECTION")
        print("-" * 40)
        
        for logo_name, logo_url in self.test_logos.items():
            print(f"\n🖼️ Testing color analysis for: {logo_name}")
            print(f"Logo URL: {logo_url}")
            
            try:
                # Test AI color analysis
                color_result = ai_color_service.get_default_colors_for_products(logo_url)
                
                if color_result['success']:
                    recommended_colors = color_result['colors']
                    print(f"✅ AI recommended colors: {recommended_colors}")
                    
                    # Test if colors are reasonable
                    reasonable_colors = self._evaluate_color_selection(recommended_colors)
                    
                    if reasonable_colors:
                        print("✅ Color recommendations are reasonable")
                        self.test_results.append({
                            'test': f"Color Selection - {logo_name}",
                            'status': 'PASS',
                            'ai_colors': recommended_colors,
                            'ai_reasoning': 'Colors appropriate for youth sports'
                        })
                    else:
                        print("❌ Color recommendations seem inappropriate")
                        self.failed_tests.append({
                            'test': f"Color Selection - {logo_name}",
                            'issue': 'Inappropriate color selection',
                            'colors': recommended_colors
                        })
                else:
                    print(f"❌ AI color analysis failed: {color_result.get('error')}")
                    self.failed_tests.append({
                        'test': f"Color Selection - {logo_name}",
                        'issue': 'AI color analysis failed',
                        'error': color_result.get('error')
                    })
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Error testing color selection for {logo_name}: {e}")
                self.failed_tests.append({
                    'test': f"Color Selection - {logo_name}",
                    'issue': 'Exception occurred',
                    'error': str(e)
                })
    
    def test_mockup_generation(self):
        """Test end-to-end mockup generation"""
        print("\n🖼️ TESTING MOCKUP GENERATION")
        print("-" * 40)
        
        # Test with the first scenario and soccer logo
        scenario = self.test_scenarios[0]  # Soccer Mom - Basic Request
        logo_url = self.test_logos['soccer_logo']
        
        print(f"\n🎯 Testing complete flow: {scenario['name']}")
        print(f"Request: \"{scenario['request']}\"")
        print(f"Logo: {logo_url}")
        
        try:
            # Step 1: Product Selection
            conversation_context = {
                'sport_context': scenario['sport_context'],
                'age_group': scenario['age_group']
            }
            
            selection_result = product_selector.select_products_from_conversation(
                scenario['request'], 
                conversation_context
            )
            
            if not selection_result['success']:
                print("❌ Product selection failed")
                return
            
            selected_products = selection_result.get('selected_products', [])
            if not selected_products:
                print("❌ No products selected")
                return
            
            # Use first selected product
            product = selected_products[0]
            print(f"✅ Selected product: {product['title']}")
            
            # Step 2: Color Selection
            color_result = ai_color_service.get_default_colors_for_products(logo_url)
            
            if not color_result['success']:
                print("❌ Color selection failed")
                return
            
            recommended_colors = color_result['colors']
            product_category = product['category']
            selected_color = recommended_colors.get(product_category, 'Black')
            print(f"✅ Selected color: {selected_color}")
            
            # Step 3: Find matching variant
            variants = product.get('variants', [])
            selected_variant = None
            
            for variant in variants:
                if selected_color.lower() in variant['color'].lower():
                    selected_variant = variant
                    break
            
            if not selected_variant:
                selected_variant = variants[0] if variants else None
            
            if not selected_variant:
                print("❌ No variant found")
                return
            
            print(f"✅ Selected variant: {selected_variant['color']} / {selected_variant.get('size', 'N/A')}")
            
            # Step 4: Create mockup
            design_request = {
                'blueprint_id': product['blueprint_id'],
                'print_provider_id': product['print_provider_id'],
                'variant_id': selected_variant['id'],
                'print_areas': {
                    'front': logo_url
                }
            }
            
            print(f"🔄 Creating mockup via Printify API...")
            mockup_result = printify_service.create_design_mockup(design_request)
            
            if mockup_result['success']:
                mockup_url = mockup_result['mockup_url']
                print(f"✅ Mockup created: {mockup_url}")
                
                # Analyze mockup quality
                quality_score = self._analyze_mockup_quality(mockup_url, scenario, product, selected_color)
                
                self.test_results.append({
                    'test': 'End-to-End Mockup Generation',
                    'status': 'PASS',
                    'mockup_url': mockup_url,
                    'product': product['title'],
                    'color': selected_variant['color'],
                    'quality_score': quality_score
                })
                
                print(f"✅ Mockup quality score: {quality_score}/10")
                
            else:
                print(f"❌ Mockup creation failed: {mockup_result.get('error')}")
                self.failed_tests.append({
                    'test': 'End-to-End Mockup Generation',
                    'issue': 'Mockup creation failed',
                    'error': mockup_result.get('error')
                })
            
        except Exception as e:
            print(f"❌ Error in mockup generation test: {e}")
            self.failed_tests.append({
                'test': 'End-to-End Mockup Generation',
                'issue': 'Exception occurred',
                'error': str(e)
            })
    
    def test_mockup_quality_analysis(self):
        """Analyze mockup images using AI"""
        print("\n🔍 TESTING MOCKUP QUALITY ANALYSIS")
        print("-" * 40)
        
        # Test with a few different product/color combinations
        test_combinations = [
            {'product_type': 'tshirt', 'color': 'Navy', 'context': 'youth soccer'},
            {'product_type': 'hoodie', 'color': 'Black', 'context': 'youth basketball'},
            {'product_type': 'headwear', 'color': 'Red', 'context': 'youth baseball'}
        ]
        
        for combo in test_combinations:
            print(f"\n🎯 Testing quality for: {combo['product_type']} in {combo['color']}")
            
            try:
                # Get products of this type
                products = product_service.get_products_by_category(combo['product_type'])
                
                if not products:
                    print(f"❌ No products found for {combo['product_type']}")
                    continue
                
                # Use most popular product
                product = products[0]
                
                # Find variant with requested color
                variants = product.get('variants', [])
                selected_variant = None
                
                for variant in variants:
                    if combo['color'].lower() in variant['color'].lower():
                        selected_variant = variant
                        break
                
                if not selected_variant:
                    print(f"❌ No {combo['color']} variant found")
                    continue
                
                # Create a quick mockup
                design_request = {
                    'blueprint_id': product['blueprint_id'],
                    'print_provider_id': product['print_provider_id'],
                    'variant_id': selected_variant['id'],
                    'print_areas': {
                        'front': self.test_logos['soccer_logo']  # Use default logo
                    }
                }
                
                mockup_result = printify_service.create_design_mockup(design_request)
                
                if mockup_result['success']:
                    mockup_url = mockup_result['mockup_url']
                    print(f"✅ Created mockup: {mockup_url}")
                    
                    # Use AI to analyze the mockup image
                    analysis = self._ai_analyze_mockup_image(mockup_url, combo)
                    
                    print(f"🤖 AI Analysis: {analysis['assessment']}")
                    print(f"📊 Quality Score: {analysis['quality_score']}/10")
                    
                    if analysis['quality_score'] >= 7:
                        print("✅ High quality mockup")
                        self.test_results.append({
                            'test': f"Mockup Quality - {combo['product_type']} {combo['color']}",
                            'status': 'PASS',
                            'quality_score': analysis['quality_score'],
                            'ai_assessment': analysis['assessment']
                        })
                    else:
                        print("⚠️ Low quality mockup - needs attention")
                        self.failed_tests.append({
                            'test': f"Mockup Quality - {combo['product_type']} {combo['color']}",
                            'issue': 'Low quality score',
                            'quality_score': analysis['quality_score'],
                            'ai_assessment': analysis['assessment']
                        })
                else:
                    print(f"❌ Failed to create mockup: {mockup_result.get('error')}")
                
                time.sleep(2)  # Rate limiting for API calls
                
            except Exception as e:
                print(f"❌ Error testing quality for {combo}: {e}")
    
    def _evaluate_product_selection(self, scenario: Dict, selected_categories: List[str], selected_products: List[Dict]) -> bool:
        """Evaluate if AI product selection is reasonable"""
        sport_context = scenario['sport_context'].lower()
        age_group = scenario['age_group'].lower()
        
        # Check if selected categories make sense for the sport
        sport_appropriate_products = {
            'soccer': ['tshirt', 'hoodie', 'headwear', 'long_sleeve'],
            'basketball': ['tshirt', 'tank', 'hoodie', 'headwear'],
            'baseball': ['tshirt', 'headwear', 'hoodie', 'long_sleeve'],
            'volleyball': ['tank', 'tshirt', 'hoodie'],
            'tennis': ['tshirt', 'tank', 'headwear']
        }
        
        appropriate_for_sport = sport_appropriate_products.get(sport_context, ['tshirt', 'hoodie'])
        
        # Check if at least one selected category is appropriate
        has_appropriate_selection = any(cat in appropriate_for_sport for cat in selected_categories)
        
        # Check if products have youth/kids sizing (for youth context)
        has_youth_sizing = True
        if age_group in ['youth', 'kids']:
            for product in selected_products:
                product_title = product.get('title', '').lower()
                if not any(keyword in product_title for keyword in ['youth', 'kids', 'junior', 'toddler', 'unisex']):
                    has_youth_sizing = False
                    break
        
        return has_appropriate_selection and has_youth_sizing
    
    def _evaluate_color_selection(self, recommended_colors: Dict) -> bool:
        """Evaluate if AI color selection is reasonable"""
        # Check that colors are appropriate for youth sports
        inappropriate_colors = ['neon pink', 'bright purple', 'lime green', 'hot pink']
        appropriate_colors = ['black', 'white', 'navy', 'red', 'blue', 'green', 'gray', 'grey']
        
        for product_type, color in recommended_colors.items():
            color_lower = color.lower()
            
            # Check if color is inappropriate
            if any(bad_color in color_lower for bad_color in inappropriate_colors):
                return False
            
            # Prefer if color is in appropriate list
            if not any(good_color in color_lower for good_color in appropriate_colors):
                # Not necessarily bad, but should be reasonable
                pass
        
        return True
    
    def _analyze_mockup_quality(self, mockup_url: str, scenario: Dict, product: Dict, color: str) -> int:
        """Analyze mockup quality (basic checks)"""
        quality_score = 8  # Start with high score
        
        try:
            # Check if URL is accessible
            response = requests.head(mockup_url, timeout=10)
            if response.status_code != 200:
                quality_score -= 3
                
            # Check if it's an image
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                quality_score -= 2
                
            # Additional checks could include:
            # - Image size validation
            # - Color accuracy
            # - Logo placement
            # But for now, we'll use AI analysis
            
        except Exception as e:
            print(f"⚠️ Error checking mockup URL: {e}")
            quality_score -= 2
        
        return max(1, quality_score)
    
    def _ai_analyze_mockup_image(self, mockup_url: str, combo: Dict) -> Dict:
        """Use AI to analyze mockup image quality"""
        try:
            system_prompt = """You are an expert in youth sports merchandise quality assessment.
            
            Analyze the mockup image and evaluate:
            1. Overall visual quality and professionalism
            2. Logo placement and size appropriateness
            3. Color accuracy and appeal for youth sports
            4. Product appropriateness for the context
            5. Overall appeal to parents buying for their kids
            
            Respond in JSON format:
            {
                "quality_score": 1-10,
                "assessment": "Brief assessment of the mockup quality and appropriateness",
                "strengths": ["list", "of", "strengths"],
                "concerns": ["list", "of", "any", "concerns"]
            }"""
            
            user_prompt = f"""Analyze this youth sports mockup:
            
            URL: {mockup_url}
            Product Type: {combo['product_type']}
            Color: {combo['color']}
            Context: {combo['context']}
            
            This will be shown to parents considering purchasing team merchandise for their children."""
            
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
            print(f"⚠️ Error in AI mockup analysis: {e}")
            return {
                "quality_score": 5,
                "assessment": "Could not analyze mockup due to technical error",
                "strengths": [],
                "concerns": ["Analysis failed"]
            }
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("🧠 AI INTELLIGENCE TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results) + len(self.failed_tests)
        passed_tests = len(self.test_results)
        failed_tests = len(self.failed_tests)
        
        print(f"\n📊 SUMMARY:")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
        
        if self.test_results:
            print(f"\n✅ PASSED TESTS:")
            for result in self.test_results:
                print(f"  • {result['test']}: {result['status']}")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for failure in self.failed_tests:
                print(f"  • {failure['test']}: {failure['issue']}")
                if 'error' in failure:
                    print(f"    Error: {failure['error']}")
        
        print(f"\n🎯 AI PERFORMANCE ANALYSIS:")
        
        # Analyze AI decision patterns
        product_selection_tests = [r for r in self.test_results if 'Product Selection' in r['test']]
        color_selection_tests = [r for r in self.test_results if 'Color Selection' in r['test']]
        mockup_tests = [r for r in self.test_results if 'Mockup' in r['test']]
        
        print(f"  • Product Selection AI: {len(product_selection_tests)} successful tests")
        print(f"  • Color Selection AI: {len(color_selection_tests)} successful tests")
        print(f"  • Mockup Generation: {len(mockup_tests)} successful tests")
        
        # Calculate quality scores
        quality_scores = [r.get('quality_score', 0) for r in self.test_results if 'quality_score' in r]
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            print(f"  • Average Mockup Quality: {avg_quality:.1f}/10")
        
        print(f"\n💡 RECOMMENDATIONS:")
        
        if failed_tests == 0:
            print("  • 🎉 All AI systems performing excellently!")
            print("  • ✅ Product selection logic is working well")
            print("  • ✅ Color matching is appropriate")
            print("  • ✅ Mockup generation is successful")
        else:
            if any('Product Selection' in f['test'] for f in self.failed_tests):
                print("  • ⚠️ Consider improving product selection AI prompts")
            if any('Color Selection' in f['test'] for f in self.failed_tests):
                print("  • ⚠️ Consider refining color analysis algorithms")
            if any('Mockup' in f['test'] for f in self.failed_tests):
                print("  • ⚠️ Check Printify API integration and error handling")
        
        print("\n" + "=" * 60)


def main():
    """Run the AI intelligence test suite"""
    tester = AIIntelligenceTest()
    tester.run_all_tests()


if __name__ == "__main__":
    main()