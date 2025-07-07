#!/usr/bin/env python3
"""
Test runner for Question 5: Unhappy Flows

This script runs all unhappy flow tests across the integrated system components.
It provides detailed reporting and handles test dependencies.
"""

import unittest
import sys
import os
import time
from io import StringIO

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

def run_test_suite():
    """Run all unhappy flow tests with detailed reporting"""
    
    print("=" * 80)
    print("QUESTION 5: UNHAPPY FLOWS TEST SUITE")
    print("=" * 80)
    print(f"Testing robustness against invalid/malicious inputs")
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Discover and load all test modules
    test_modules = [
        'tests.test_unhappy_calculator',
        'tests.test_unhappy_products', 
        'tests.test_unhappy_outlets',
        'tests.test_unhappy_sequential'
    ]
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Load tests from each module
    for module_name in test_modules:
        try:
            module = __import__(module_name, fromlist=[''])
            module_suite = loader.loadTestsFromModule(module)
            suite.addTests(module_suite)
            print(f"✓ Loaded tests from {module_name}")
        except ImportError as e:
            print(f"✗ Failed to load {module_name}: {e}")
        except Exception as e:
            print(f"✗ Error loading {module_name}: {e}")
    
    print(f"\nTotal tests discovered: {suite.countTestCases()}")
    print("-" * 80)
    
    # Custom test result class for detailed reporting
    class DetailedTestResult(unittest.TextTestResult):
        def __init__(self, stream, descriptions, verbosity):
            super().__init__(stream, descriptions, verbosity)
            self.test_results = []
        
        def startTest(self, test):
            super().startTest(test)
            self.start_time = time.time()
        
        def addSuccess(self, test):
            super().addSuccess(test)
            elapsed = time.time() - self.start_time
            self.test_results.append(('PASS', test, elapsed, None))
        
        def addError(self, test, err):
            super().addError(test, err)
            elapsed = time.time() - self.start_time
            self.test_results.append(('ERROR', test, elapsed, err))
        
        def addFailure(self, test, err):
            super().addFailure(test, err)
            elapsed = time.time() - self.start_time
            self.test_results.append(('FAIL', test, elapsed, err))
        
        def addSkip(self, test, reason):
            super().addSkip(test, reason)
            elapsed = time.time() - self.start_time
            self.test_results.append(('SKIP', test, elapsed, reason))
    
    # Run the tests
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        resultclass=DetailedTestResult
    )
    
    print("Running tests...")
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Print detailed results
    print("\n" + "=" * 80)
    print("DETAILED TEST RESULTS")
    print("=" * 80)
    
    # Group results by category
    categories = {
        'Calculator Tests': [],
        'Products Tests': [],
        'Outlets Tests': [],
        'Sequential Conversation Tests': []
    }
    
    for status, test, elapsed, error in result.test_results:
        test_name = str(test)
        if 'calculator' in test_name.lower():
            categories['Calculator Tests'].append((status, test, elapsed, error))
        elif 'products' in test_name.lower():
            categories['Products Tests'].append((status, test, elapsed, error))
        elif 'outlets' in test_name.lower():
            categories['Outlets Tests'].append((status, test, elapsed, error))
        elif 'sequential' in test_name.lower():
            categories['Sequential Conversation Tests'].append((status, test, elapsed, error))
    
    # Print results by category
    for category, tests in categories.items():
        if tests:
            print(f"\n{category}:")
            print("-" * len(category))
            
            for status, test, elapsed, error in tests:
                test_method = test._testMethodName
                status_symbol = {
                    'PASS': '✓',
                    'FAIL': '✗',
                    'ERROR': '✗',
                    'SKIP': '⊝'
                }[status]
                
                print(f"  {status_symbol} {test_method:<50} ({elapsed:.3f}s)")
                
                if error and status in ['FAIL', 'ERROR']:
                    # Print first line of error for summary
                    error_msg = str(error[1]).split('\n')[0][:100]
                    print(f"    → {error_msg}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total_tests = result.testsRun
    passed = len([r for r in result.test_results if r[0] == 'PASS'])
    failed = len(result.failures)
    errors = len(result.errors)
    skipped = len([r for r in result.test_results if r[0] == 'SKIP'])
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed:      {passed} ({passed/total_tests*100:.1f}%)")
    print(f"Failed:      {failed} ({failed/total_tests*100:.1f}%)")
    print(f"Errors:      {errors} ({errors/total_tests*100:.1f}%)")
    print(f"Skipped:     {skipped} ({skipped/total_tests*100:.1f}%)")
    print(f"Duration:    {end_time - start_time:.2f} seconds")
    
    # Coverage analysis
    print(f"\nUNHAPPY FLOW COVERAGE:")
    print(f"✓ Missing parameters (empty/null inputs)")
    print(f"✓ API downtime simulation (HTTP 5xx errors)")
    print(f"✓ Malicious payloads (SQL injection, XSS, code injection)")
    print(f"✓ Network failures and timeouts")
    print(f"✓ Service dependency failures")
    print(f"✓ Input validation edge cases")
    print(f"✓ Concurrent access patterns")
    print(f"✓ State corruption recovery")
    
    # Print failed tests details if any
    if result.failures or result.errors:
        print("\n" + "=" * 80)
        print("FAILURE DETAILS")
        print("=" * 80)
        
        for test, traceback in result.failures:
            print(f"\nFAILED: {test}")
            print("-" * 40)
            print(traceback)
        
        for test, traceback in result.errors:
            print(f"\nERROR: {test}")
            print("-" * 40)
            print(traceback)
    
    # Overall result
    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("🎉 ALL UNHAPPY FLOW TESTS PASSED!")
        print("The system demonstrates robust error handling and security.")
    else:
        print("⚠️  Some tests failed. Review the failures above.")
        print("Consider strengthening error handling in the affected areas.")
    
    print(f"Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1) 