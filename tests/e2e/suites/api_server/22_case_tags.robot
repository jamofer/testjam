*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    I clean up the current project


*** Test Cases ***
Adding tags to a test case persists them
    # Given
    I am authenticated as admin
    I create a project named Case-Tags
    I create a suite named main
    I create a test case named login_flow

    # When
    I add tags smoke, regression to the test case

    # Then
    The test case should have tags smoke, regression

Replacing tags on a test case overwrites the previous set
    # Given
    I am authenticated as admin
    I create a project named Case-Tags-Replace
    I create a suite named main
    I create a test case named retry_flow
    I add tags smoke to the test case

    # When
    I add tags critical, ui to the test case

    # Then
    The test case should have tags critical, ui
