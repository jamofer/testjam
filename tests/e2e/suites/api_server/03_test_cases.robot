*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Test Cases ***
Create a test case inside a suite
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Case Project
    I create a suite named Login Suite
    # When
    I create a test case named Happy Path Login
    # Then
    The suite should have 1 test cases
    The test case name should be Happy Path Login

Rename a test case
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Rename Case Project
    I create a suite named Suite A
    I create a test case named Original Name
    # When
    I rename the test case to Refactored Name
    # Then
    The test case name should be Refactored Name

Delete a test case
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Delete Case Project
    I create a suite named Suite B
    I create a test case named Disposable Case
    # When
    I delete the test case
    # Then
    The test case should no longer exist

Test case with action steps
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Steps Project
    I create a suite named Steps Suite
    I create a test case named Multi-Step Case
    # When
    I add a step Open the login page to the test case
    I add a step Enter valid credentials to the test case
    I add a step Submit the form to the test case
    # Then
    The test case should have 3 steps

Test case with setup and teardown steps
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Lifecycle Project
    I create a suite named Lifecycle Suite
    I create a test case named Lifecycle Case
    # When
    I add setup step Prepare test data to the test case
    I add action step Execute the main flow to the test case
    I add teardown step Clean up test data to the test case
    # Then
    The test case should have 3 steps

Test case with external ID for automation matching
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Automation Project
    I create a suite named Automation Suite
    I create a test case named Automated Login with external id com.example.LoginTest.testHappyPath
    # Then
    The test case name should be Automated Login
