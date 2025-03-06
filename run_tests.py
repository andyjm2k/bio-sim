#!/usr/bin/env python3
"""
Master Unit Test Runner for Bio-Sim Project

This script discovers and runs all unit tests in the project, including tests in the
'tests/' directory and in the project root. It provides options for running specific 
test modules, classes, or test methods.

Usage:
    python run_tests.py                  # Run all tests
    python run_tests.py -v                # Run all tests with verbose output
    python run_tests.py tests/test_file.py  # Run specific test file
    python run_tests.py -p pattern        # Run tests matching pattern
"""

import unittest
import sys
import os
import time
import argparse
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

def discover_tests(start_dir='.', pattern='test_*.py'):
    """
    Discover all tests in the given directory with the given pattern.
    
    Args:
        start_dir (str): Directory to start discovery from
        pattern (str): Pattern to match test files
        
    Returns:
        unittest.TestSuite: Test suite containing all discovered tests
    """
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir, pattern=pattern)
    return suite

def run_specific_test(test_path):
    """
    Run a specific test file, class, or method.
    
    Args:
        test_path (str): Path to test file, class, or method
        
    Returns:
        unittest.TestSuite: Test suite for the specified test
    """
    loader = unittest.TestLoader()
    
    if os.path.isfile(test_path):
        # Load tests from file
        module_name = test_path.replace('/', '.').replace('\\', '.').rstrip('.py')
        if module_name.startswith('.'):
            module_name = module_name[1:]
        return loader.loadTestsFromName(module_name)
    else:
        # Try to load the test by name (might be a class or method)
        try:
            return loader.loadTestsFromName(test_path)
        except (ImportError, AttributeError):
            print(f"{Fore.RED}Error: Could not find test: {test_path}{Style.RESET_ALL}")
            sys.exit(1)

def count_tests(suite):
    """
    Count the number of tests in a test suite.
    
    Args:
        suite (unittest.TestSuite): Test suite to count
        
    Returns:
        int: Number of tests in the suite
    """
    counter = 0
    for test in suite:
        if hasattr(test, '_tests'):
            counter += count_tests(test)
        else:
            counter += 1
    return counter

def print_summary(result, duration):
    """
    Print a summary of the test results.
    
    Args:
        result (unittest.TestResult): Result of the test run
        duration (float): Duration of the test run in seconds
    """
    print("\n" + "=" * 70)
    print(f"{Fore.CYAN}TEST SUMMARY:{Style.RESET_ALL}")
    print(f"Ran {result.testsRun} tests in {duration:.2f} seconds")
    
    if result.wasSuccessful():
        print(f"{Fore.GREEN}SUCCESS: All tests passed!{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}FAILURE: Some tests failed!{Style.RESET_ALL}")
    
    if result.failures:
        print(f"\n{Fore.RED}Failures ({len(result.failures)}):{Style.RESET_ALL}")
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"{i}. {test}")
    
    if result.errors:
        print(f"\n{Fore.RED}Errors ({len(result.errors)}):{Style.RESET_ALL}")
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"{i}. {test}")
    
    if result.skipped:
        print(f"\n{Fore.YELLOW}Skipped ({len(result.skipped)}):{Style.RESET_ALL}")
        for i, (test, reason) in enumerate(result.skipped, 1):
            print(f"{i}. {test} - {reason}")
    
    print("=" * 70)

def main():
    """
    Main function to parse arguments and run tests.
    """
    parser = argparse.ArgumentParser(description='Run unit tests for the Bio-Sim project')
    parser.add_argument('test', nargs='?', help='Specific test file, class, or method to run')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-p', '--pattern', default='test_*.py', help='Pattern to match test files')
    args = parser.parse_args()
    
    # Set verbosity level
    verbosity = 2 if args.verbose else 1
    
    # Create test runner
    runner = unittest.TextTestRunner(verbosity=verbosity)
    
    # Discover or load specific tests
    if args.test:
        suite = run_specific_test(args.test)
    else:
        # Discover tests in both the tests directory and the project root
        test_dirs = ['tests', '.']
        suite = unittest.TestSuite()
        for directory in test_dirs:
            if os.path.isdir(directory):
                discovered_suite = discover_tests(directory, args.pattern)
                suite.addTest(discovered_suite)
    
    num_tests = count_tests(suite)
    print(f"{Fore.CYAN}Running {num_tests} tests...{Style.RESET_ALL}")
    
    # Run the tests and time it
    start_time = time.time()
    result = runner.run(suite)
    duration = time.time() - start_time
    
    # Print summary
    print_summary(result, duration)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(main()) 