#!/usr/bin/env python3
"""
Main testing script for Integrity Auditor models
Run this before using frontend/backend to verify all models work correctly
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from integrity_auditor import (
    TextAuditor,
    CodeAuditor,
    StylometryAnalyzer,
    DatasetManager,
    IntegrityLogger,
    ensure_directory
)


class ModelTester:
    """Test all Integrity Auditor models"""
    
    def __init__(self):
        self.test_results = {}
        self.logger = IntegrityLogger("./logs/model_tests.log")
        print("🧪 INTEGRITY AUDITOR MODEL TESTER")
        print("=" * 60)
    
    def run_all_tests(self):
        """Run all model tests"""
        print("\n🔍 Running comprehensive model tests...")
        
        # 1. Test Text Auditor (AI vs Human detection)
        print("\n1️⃣ Testing Text Auditor (Anti-LLM Detection)...")
        text_test_result = self.test_text_auditor()
        self.test_results['text_auditor'] = text_test_result
        
        # 2. Test Code Auditor (Plagiarism detection)
        print("\n2️⃣ Testing Code Auditor (AST Plagiarism)...")
        code_test_result = self.test_code_auditor()
        self.test_results['code_auditor'] = code_test_result
        
        # 3. Test Stylometry Analyzer
        print("\n3️⃣ Testing Stylometry Analyzer (Author Identification)...")
        stylo_test_result = self.test_stylometry_analyzer()
        self.test_results['stylometry'] = stylo_test_result
        
        # 4. Test Dataset Manager
        print("\n4️⃣ Testing Dataset Manager...")
        dataset_test_result = self.test_dataset_manager()
        self.test_results['dataset_manager'] = dataset_test_result
        
        # 5. Test Utilities
        print("\n5️⃣ Testing Utilities...")
        util_test_result = self.test_utilities()
        self.test_results['utilities'] = util_test_result
        
        # 6. Generate Summary Report
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY REPORT")
        print("=" * 60)
        self.generate_summary()
        
        # Log results
        self.logger.log_audit("model_tests", self.test_results)
        
        return self.test_results
    
    def test_text_auditor(self):
        """Test Text Auditor model"""
        try:
            print("   Loading Text Auditor...")
            text_auditor = TextAuditor()
            
            # Test texts
            test_texts = {
                "human_like": (
                    "The quick brown fox jumps over the lazy dog. "
                    "This is a classic English pangram that contains every letter "
                    "of the alphabet. It's often used for typing practice and "
                    "testing typewriters and computer keyboards."
                ),
                "ai_like": (
                    "The felis catus, commonly referred to as the domestic cat, "
                    "is a small carnivorous mammal. It is the only domesticated "
                    "species in the family Felidae. Domestic cats are valued by "
                    "humans for companionship and their ability to hunt rodents."
                )
            }
            
            results = {}
            for name, text in test_texts.items():
                print(f"   Analyzing {name} text...")
                result = text_auditor.analyze_text(text)
                results[name] = result
                
                print(f"     Verdict: {result.get('verdict', 'N/A')}")
                print(f"     AI Confidence: {result.get('ai_confidence', 0):.2f}%")
                print(f"     Human Confidence: {result.get('human_confidence', 0):.2f}%")
            
            # Check if model loaded properly
            model_loaded = text_auditor.model is not None
            tokenizer_loaded = text_auditor.tokenizer is not None
            
            test_passed = model_loaded and tokenizer_loaded
            status = "✅ PASS" if test_passed else "❌ FAIL"
            
            return {
                "status": status,
                "model_loaded": model_loaded,
                "tokenizer_loaded": tokenizer_loaded,
                "test_results": results,
                "details": "Text Auditor functional" if test_passed else "Text Auditor failed to load"
            }
            
        except Exception as e:
            return {
                "status": "❌ FAIL",
                "error": str(e),
                "details": "Text Auditor test failed with exception"
            }
    
    def test_code_auditor(self):
        """Test Code Auditor model"""
        try:
            print("   Loading Code Auditor...")
            code_auditor = CodeAuditor()
            
            # Create test Python code
            test_code_1 = """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total = total + num
    return total
"""
            
            test_code_2 = """
def add_values(values):
    result = 0
    for value in values:
        result = result + value
    return result
"""
            
            test_code_3 = """
def multiply(a, b):
    return a * b
"""
            
            print("   Testing code plagiarism detection...")
            
            # Test similar code (should have high similarity)
            result1 = code_auditor.analyze_python(test_code_1, test_code_2)
            print(f"     Similar code similarity: {result1.get('similarity_percentage', 0):.2f}%")
            
            # Test different code (should have low similarity)
            result2 = code_auditor.analyze_python(test_code_1, test_code_3)
            print(f"     Different code similarity: {result2.get('similarity_percentage', 0):.2f}%")
            
            # Create temporary test files
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f1:
                f1.write(test_code_1)
                temp_file1 = f1.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f2:
                f2.write(test_code_2)
                temp_file2 = f2.name
            
            # Test file analysis
            result3 = code_auditor.analyze_files(temp_file1, temp_file2)
            print(f"     File analysis similarity: {result3.get('similarity_percentage', 0):.2f}%")
            
            # Cleanup
            os.unlink(temp_file1)
            os.unlink(temp_file2)
            
            test_passed = all(
                'similarity_percentage' in r 
                for r in [result1, result2, result3]
            )
            status = "✅ PASS" if test_passed else "❌ FAIL"
            
            return {
                "status": status,
                "test_results": {
                    "similar_code": result1,
                    "different_code": result2,
                    "file_analysis": result3
                },
                "details": "Code Auditor functional" if test_passed else "Code Auditor tests failed"
            }
            
        except Exception as e:
            return {
                "status": "❌ FAIL",
                "error": str(e),
                "details": "Code Auditor test failed with exception"
            }
    
    def test_stylometry_analyzer(self):
        """Test Stylometry Analyzer"""
        try:
            print("   Loading Stylometry Analyzer...")
            stylometry = StylometryAnalyzer()
            
            # Test text for style analysis
            test_text = """
            Machine learning is a fascinating field that combines statistics,
            computer science, and domain expertise. Researchers in this area
            often develop algorithms that can learn from data without being
            explicitly programmed. The applications are numerous, ranging from
            image recognition to natural language processing.
            """
            
            print("   Extracting stylometric features...")
            features = stylometry.extract_features(test_text)
            
            print(f"     Word count: {features.get('word_count', 0)}")
            print(f"     Sentence count: {features.get('sentence_count', 0)}")
            print(f"     Avg word length: {features.get('avg_word_length', 0):.2f}")
            
            # Check if model can be trained (simulated)
            try:
                # Try to load existing model
                import joblib
                model_path = "./models/stylometry_model.pkl"
                if os.path.exists(model_path):
                    print("     Found pre-trained stylometry model")
                    model_loaded = True
                else:
                    print("     No pre-trained model found (training required)")
                    model_loaded = False
            except:
                model_loaded = False
            
            test_passed = len(features) > 0
            status = "✅ PASS" if test_passed else "❌ FAIL"
            
            return {
                "status": status,
                "features_extracted": len(features),
                "sample_features": {
                    "word_count": features.get('word_count'),
                    "sentence_count": features.get('sentence_count'),
                    "avg_word_length": features.get('avg_word_length')
                },
                "model_loaded": model_loaded,
                "details": "Stylometry Analyzer functional" if test_passed else "Feature extraction failed"
            }
            
        except Exception as e:
            return {
                "status": "❌ FAIL",
                "error": str(e),
                "details": "Stylometry Analyzer test failed with exception"
            }
    
    def test_dataset_manager(self):
        """Test Dataset Manager"""
        try:
            print("   Loading Dataset Manager...")
            dataset_manager = DatasetManager()
            
            # Get dataset info
            datasets = dataset_manager.get_dataset_info()
            
            print("   Available datasets:")
            for category, ds_list in datasets.items():
                print(f"     {category.upper()}:")
                for ds_name, ds_desc in ds_list.items():
                    print(f"       - {ds_name}: {ds_desc}")
            
            # Test HC3 dataset loading (small sample)
            print("\n   Testing HC3 dataset loading...")
            try:
                texts, labels = dataset_manager.load_hc3_dataset(sample_size=10)
                hc3_loaded = len(texts) > 0
                print(f"     Loaded {len(texts)} samples from HC3")
            except Exception as e:
                print(f"     HC3 loading failed: {e}")
                hc3_loaded = False
            
            test_passed = len(datasets) > 0
            status = "✅ PASS" if test_passed else "❌ FAIL"
            
            return {
                "status": status,
                "datasets_available": len(datasets),
                "hc3_loaded": hc3_loaded,
                "dataset_categories": list(datasets.keys()),
                "details": "Dataset Manager functional" if test_passed else "No datasets available"
            }
            
        except Exception as e:
            return {
                "status": "❌ FAIL",
                "error": str(e),
                "details": "Dataset Manager test failed with exception"
            }
    
    def test_utilities(self):
        """Test utility functions"""
        try:
            print("   Testing utility functions...")
            
            from integrity_auditor.utils import (
                generate_report_id,
                calculate_text_hash,
                format_percentage,
                ensure_directory
            )
            
            # Test report ID generation
            report_id = generate_report_id()
            print(f"     Generated Report ID: {report_id}")
            
            # Test text hash
            text_hash = calculate_text_hash("Test text")
            print(f"     Text hash: {text_hash}")
            
            # Test percentage formatting
            formatted = format_percentage(85.6789)
            print(f"     Formatted percentage: {formatted}")
            
            # Test directory creation
            test_dir = "./test_temp_dir"
            ensure_directory(test_dir)
            dir_exists = os.path.exists(test_dir)
            print(f"     Directory created: {dir_exists}")
            
            # Cleanup
            if dir_exists:
                import shutil
                shutil.rmtree(test_dir)
            
            # Test logger
            logger = IntegrityLogger("./logs/test.log")
            logger.log_audit("test", {"message": "Test log entry"})
            print("     Logger test completed")
            
            test_passed = all([
                report_id.startswith("REPORT_"),
                len(text_hash) == 32,
                formatted == "85.68%",
                True  # If we got here without exceptions
            ])
            
            status = "✅ PASS" if test_passed else "❌ FAIL"
            
            return {
                "status": status,
                "report_id_generated": report_id.startswith("REPORT_"),
                "hash_calculated": len(text_hash) == 32,
                "percentage_formatted": formatted == "85.68%",
                "logger_working": True,
                "details": "Utilities functional" if test_passed else "Utility tests failed"
            }
            
        except Exception as e:
            return {
                "status": "❌ FAIL",
                "error": str(e),
                "details": "Utilities test failed with exception"
            }
    
    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() 
                          if r.get('status', '').startswith('✅'))
        failed_tests = total_tests - passed_tests
        
        print(f"\n📈 TEST RESULTS SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📊 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Detailed results
        print("\n🔍 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status = result.get('status', '❓ UNKNOWN')
            details = result.get('details', 'No details')
            print(f"   {test_name.upper():<20} {status:<10} {details}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if failed_tests == 0:
            print("   All models are working correctly! ✅")
            print("   You can proceed with frontend/backend integration.")
        else:
            print("   Some models need attention:")
            for test_name, result in self.test_results.items():
                if result.get('status', '').startswith('❌'):
                    print(f"   - Fix {test_name}: {result.get('details', 'Unknown error')}")
            print("\n   ⚠️  Fix the issues above before proceeding with integration.")
        
        # Save results to file
        self.save_test_report()
    
    def save_test_report(self):
        """Save test results to JSON file"""
        try:
            from integrity_auditor.utils import save_analysis_result
            filename = save_analysis_result(self.test_results, "./reports/model_test_report.json")
            print(f"\n📄 Test report saved to: {filename}")
        except Exception as e:
            print(f"\n⚠️  Could not save test report: {e}")
    
    def check_dependencies(self):
        """Check required dependencies"""
        print("\n📦 Checking dependencies...")
        
        dependencies = [
            ("torch", "PyTorch"),
            ("transformers", "Hugging Face Transformers"),
            ("datasets", "Hugging Face Datasets"),
            ("sklearn", "scikit-learn"),
            ("nltk", "NLTK"),
            ("flask", "Flask"),
        ]
        
        missing = []
        for import_name, display_name in dependencies:
            try:
                __import__(import_name)
                print(f"   ✅ {display_name}")
            except ImportError:
                missing.append(display_name)
                print(f"   ❌ {display_name} (missing)")
        
        if missing:
            print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
            print("   Install with: pip install " + " ".join(missing))
            return False
        else:
            print("\n✅ All dependencies installed!")
            return True


def main():
    """Main function"""
    print("🚀 Integrity Auditor Model Testing Script")
    print("=" * 60)
    print("\nThis script tests all AI models before frontend/backend integration.")
    print("Make sure you have run the training script first if models are missing.\n")
    
    # Create necessary directories
    ensure_directory("./models")
    ensure_directory("./logs")
    ensure_directory("./reports")
    
    # Check dependencies
    tester = ModelTester()
    
    print("🔍 Checking system requirements...")
    dependencies_ok = tester.check_dependencies()
    
    if not dependencies_ok:
        response = input("\n⚠️  Some dependencies are missing. Continue testing anyway? (y/n): ")
        if response.lower() != 'y':
            print("❌ Exiting. Please install missing dependencies first.")
            return
    
    # Run tests
    print("\n" + "=" * 60)
    print("Starting model tests...")
    print("=" * 60)
    
    try:
        results = tester.run_all_tests()
        
        # Final verdict
        passed = all(r.get('status', '').startswith('✅') 
                    for r in results.values())
        
        print("\n" + "=" * 60)
        if passed:
            print("🎉 ALL MODELS ARE READY FOR INTEGRATION! 🎉")
            print("You can now:")
            print("1. Start the backend: python backend/app.py")
            print("2. Open frontend in browser: http://localhost:5000")
            print("3. Begin using the Integrity Auditor system")
        else:
            print("⚠️  SOME MODELS NEED ATTENTION")
            print("Please fix the failed tests before proceeding with integration.")
        
        print("=" * 60)
        
        # Return exit code
        return 0 if passed else 1
        
    except KeyboardInterrupt:
        print("\n\n❌ Testing interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)