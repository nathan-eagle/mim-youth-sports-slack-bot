#!/usr/bin/env python3
"""
Comprehensive integration tests for the updated MiM system.
Tests both the Python backend and validates frontend compatibility.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import logging

# Import the updated services
from product_service import ProductService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestTop3ProductCache(unittest.TestCase):
    """Test the top3 product cache and updated product service"""
    
    def setUp(self):
        """Set up test environment"""
        self.cache_file = "top3_product_cache_optimized.json"
        self.assertTrue(os.path.exists(self.cache_file), f"Cache file {self.cache_file} not found")
        
        # Load cache data for validation
        with open(self.cache_file, 'r') as f:
            self.cache_data = json.load(f)
        
        self.product_service = ProductService(self.cache_file)
    
    def test_cache_structure(self):
        """Test that the cache has the expected structure"""
        logger.info("Testing cache structure...")
        
        # Check top-level structure
        required_keys = ['version', 'last_update', 'optimization_info', 'providers', 'products']
        for key in required_keys:
            self.assertIn(key, self.cache_data, f"Missing required key: {key}")
        
        # Check version
        self.assertEqual(self.cache_data['version'], '3.0-top3')
        
        # Check optimization info
        opt_info = self.cache_data['optimization_info']
        self.assertGreater(opt_info['optimized_products'], 0)
        self.assertIn('space_reduction', opt_info)
        
        logger.info("✅ Cache structure is valid")
    
    def test_product_data_completeness(self):
        """Test that products have all required fields"""
        logger.info("Testing product data completeness...")
        
        products = self.cache_data['products']
        self.assertGreater(len(products), 0, "No products found in cache")
        
        required_product_fields = [
            'id', 'title', 'category', 'decoration_methods', 
            'is_printify_choice', 'popularity_score', 'variants'
        ]
        
        api_complete_count = 0
        
        for product_id, product in products.items():
            # Check required fields
            for field in required_product_fields:
                self.assertIn(field, product, f"Product {product_id} missing {field}")
            
            # Check variants structure
            variants = product.get('variants', [])
            self.assertGreater(len(variants), 0, f"Product {product_id} has no variants")
            
            # Check if this product is API complete
            if (product.get('blueprint_id') and 
                product.get('print_areas') and
                any(v.get('price') for v in variants)):
                api_complete_count += 1
        
        logger.info(f"✅ Found {api_complete_count} API-complete products")
        self.assertGreater(api_complete_count, 0, "No API-complete products found")
    
    def test_product_service_loading(self):
        """Test that ProductService loads the cache correctly"""
        logger.info("Testing ProductService loading...")
        
        # Test cache loading
        self.assertTrue(self.product_service._load_cache())
        
        # Test product retrieval
        all_products = self.product_service.get_all_products()
        self.assertGreater(len(all_products), 0, "No products loaded")
        
        # Test best products (should be same as all products)
        best_products = self.product_service.get_best_products()
        self.assertEqual(len(all_products), len(best_products))
        
        logger.info(f"✅ ProductService loaded {len(all_products)} products")
    
    def test_product_variants_and_colors(self):
        """Test variant handling and color extraction"""
        logger.info("Testing product variants and colors...")
        
        all_products = self.product_service.get_all_products()
        tested_products = 0
        
        for product_id, product in all_products.items():
            # Test variant retrieval
            variants = self.product_service.get_product_variants(product_id)
            self.assertGreater(len(variants), 0, f"No variants for product {product_id}")
            
            # Test color extraction
            colors = self.product_service.get_colors_for_product(product_id)
            self.assertGreater(len(colors), 0, f"No colors for product {product_id}")
            
            # Test size extraction
            sizes = self.product_service.get_sizes_for_product(product_id)
            self.assertGreater(len(sizes), 0, f"No sizes for product {product_id}")
            
            # Test variant finding
            if colors and sizes:
                variant = self.product_service.find_variant_by_options(
                    product_id, colors[0], sizes[0]
                )
                self.assertIsNotNone(variant, f"Could not find variant for {product_id}")
            
            tested_products += 1
            
            # Limit testing to avoid long test times
            if tested_products >= 3:
                break
        
        logger.info(f"✅ Tested variants for {tested_products} products")
    
    def test_product_validation(self):
        """Test product validation functionality"""
        logger.info("Testing product validation...")
        
        all_products = self.product_service.get_all_products()
        valid_count = 0
        invalid_count = 0
        
        for product_id in all_products.keys():
            validation = self.product_service.validate_product_data(product_id)
            
            if validation['valid']:
                valid_count += 1
                # Valid products should have all required fields
                self.assertTrue(validation['has_blueprint_id'])
                self.assertTrue(validation['has_variants'])
            else:
                invalid_count += 1
                self.assertGreater(len(validation['errors']), 0)
        
        logger.info(f"✅ Validation complete: {valid_count} valid, {invalid_count} invalid")
        self.assertGreater(valid_count, 0, "No valid products found")
    
    def test_categories(self):
        """Test category-based product filtering"""
        logger.info("Testing category filtering...")
        
        # Test shirt category
        shirts = self.product_service.get_products_by_category('shirt')
        self.assertGreater(len(shirts), 0, "No shirt products found")
        
        for product in shirts.values():
            self.assertEqual(product['category'], 'shirt')
        
        # Test hoodie category  
        hoodies = self.product_service.get_products_by_category('hoodie')
        self.assertGreater(len(hoodies), 0, "No hoodie products found")
        
        for product in hoodies.values():
            self.assertEqual(product['category'], 'hoodie')
        
        logger.info(f"✅ Found {len(shirts)} shirts, {len(hoodies)} hoodies")


class TestSlackBotIntegration(unittest.TestCase):
    """Test Slack bot integration with new cache"""
    
    def setUp(self):
        """Set up Slack bot test environment"""
        self.product_service = ProductService()
    
    def test_slack_bot_imports(self):
        """Test that Slack bot can import and use ProductService"""
        logger.info("Testing Slack bot compatibility...")
        
        try:
            # Test importing slack bot modules
            import slack_bot
            import conversation_manager
            
            # Test that they can use the new ProductService
            products = self.product_service.get_all_products()
            self.assertGreater(len(products), 0)
            
            logger.info("✅ Slack bot integration compatible")
        except ImportError as e:
            self.fail(f"Failed to import Slack bot modules: {e}")
    
    @patch('slack_bot.openai')
    def test_product_recommendation_flow(self, mock_openai):
        """Test the product recommendation flow with new cache"""
        logger.info("Testing product recommendation flow...")
        
        # Mock OpenAI response
        mock_openai.ChatCompletion.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="shirt"))]
        )
        
        # Test that we can get products for recommendation
        shirts = self.product_service.get_products_by_category('shirt')
        self.assertGreater(len(shirts), 0)
        
        # Test that we can get specific product details
        first_shirt_id = list(shirts.keys())[0]
        shirt_details = self.product_service.get_product_by_id(first_shirt_id)
        self.assertIsNotNone(shirt_details)
        
        # Test color options
        colors = self.product_service.get_colors_for_product(first_shirt_id)
        self.assertGreater(len(colors), 0)
        
        logger.info(f"✅ Recommendation flow works for {len(shirts)} shirts")


class TestDropFrontendCompatibility(unittest.TestCase):
    """Test /drop frontend compatibility with new cache"""
    
    def setUp(self):
        """Set up frontend test environment"""
        self.cache_file = "drop/top3_product_cache_optimized.json"
        self.assertTrue(os.path.exists(self.cache_file), f"Drop cache file not found")
    
    def test_frontend_cache_structure(self):
        """Test that frontend cache has expected structure"""
        logger.info("Testing frontend cache compatibility...")
        
        with open(self.cache_file, 'r') as f:
            cache_data = json.load(f)
        
        # Check structure matches TypeScript interfaces
        self.assertIn('products', cache_data)
        self.assertIn('providers', cache_data)
        
        products = cache_data['products']
        if products:
            first_product = list(products.values())[0]
            
            # Check required fields for frontend
            frontend_required = ['id', 'title', 'category', 'variants']
            for field in frontend_required:
                self.assertIn(field, first_product, f"Missing frontend field: {field}")
            
            # Check variant structure
            variants = first_product.get('variants', [])
            if variants:
                first_variant = variants[0]
                variant_required = ['id', 'color', 'size', 'available']
                for field in variant_required:
                    self.assertIn(field, first_variant, f"Missing variant field: {field}")
        
        logger.info("✅ Frontend cache structure is compatible")
    
    def test_api_endpoint_compatibility(self):
        """Test that the cache structure works with existing API endpoints"""
        logger.info("Testing API endpoint compatibility...")
        
        # Test checkout API requirements
        with open(self.cache_file, 'r') as f:
            cache_data = json.load(f)
        
        products = cache_data['products']
        api_ready_products = 0
        
        for product_id, product in products.items():
            # Check if product has data needed for checkout/fulfillment
            has_blueprint = product.get('blueprint_id') is not None
            has_variants = len(product.get('variants', [])) > 0
            has_pricing = any(v.get('price') for v in product.get('variants', []))
            
            if has_blueprint and has_variants and has_pricing:
                api_ready_products += 1
        
        self.assertGreater(api_ready_products, 0, "No API-ready products found")
        logger.info(f"✅ {api_ready_products} products ready for API integration")


def run_all_tests():
    """Run all test suites"""
    print("🧪 Running MiM Integration Tests")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestTop3ProductCache,
        TestSlackBotIntegration, 
        TestDropFrontendCompatibility
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("🏁 Test Summary")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback}")
    
    if result.errors:
        print("\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n✅ All tests passed! Ready for deployment.")
    else:
        print("\n❌ Some tests failed. Please fix before deployment.")
    
    return success


if __name__ == "__main__":
    run_all_tests()