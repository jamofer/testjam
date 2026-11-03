*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Variables ***
${JUNIT_FILE}    ${CURDIR}/../../fixtures/junit_results.xml
${RF_FILE}       ${CURDIR}/../../fixtures/rf_output.xml


*** Test Cases ***
Import JUnit results and match by external ID
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named JUnit Import Project
    I create a suite named Login Test Suite
    I create a test case named Happy Path Login with external id com.example.LoginTest.testHappyPath
    I create a test case named Wrong Password with external id com.example.LoginTest.testWrongPassword
    # When
    I start an execution titled JUnit Run for the current suite
    I import JUnit results from ${JUNIT_FILE} and store the summary
    # Then
    The import should have updated 2 results

Import Robot Framework results and match by title
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named RF Import Project
    I create a suite named Login Suite
    I create a test case named Happy Path Login
    I add a step Open The Login Page to the test case
    I add a step Enter Valid Credentials to the test case
    I add a step Submit The Form to the test case
    # When
    I start an execution titled RF Run for the current suite
    I import Robot Framework results from ${RF_FILE} and store the summary
    # Then
    The import should have updated 1 results
