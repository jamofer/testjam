*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    I clean up the current project


*** Test Cases ***
Searching by query returns matching cases
    # Given
    I am authenticated as admin
    I create a project named Case-Search
    I create a suite named main
    I create a test case named login_happy_path
    I create a test case named login_failure_modes
    I create a test case named profile_update

    # When
    I search project cases for login

    # Then
    The case search result should have 2 cases
    The case search result should contain login_happy_path
    The case search result should contain login_failure_modes
    The case search result should not contain profile_update

Filtering by tag returns only matching cases
    # Given
    I am authenticated as admin
    I create a project named Case-Filter
    I create a suite named main
    I create a test case named login_smoke
    I add tags smoke to the test case
    I create a test case named login_regression
    I add tags regression to the test case
    I create a test case named login_critical
    I add tags critical, smoke to the test case

    # When
    I filter project cases by tag smoke

    # Then
    The case search result should have 2 cases
    The case search result should contain login_smoke
    The case search result should contain login_critical
    The case search result should not contain login_regression
