*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I sign in to the UI as ${ADMIN_USER} with password ${ADMIN_PASS}
Suite Teardown    I tear down the frontend suite
Test Setup        I have a fresh project named ${PROJECT_NAME}


*** Variables ***
${ADMIN_USER}      %{TESTJAM_USER=admin}
${ADMIN_PASS}      %{TESTJAM_PASS=admin123}
${PROJECT_NAME}    UI-Plans-Project


*** Test Cases ***
Creating a plan shows it in the plans list
    # Given
    I open the test plans page

    # When
    I create a test plan via the UI titled Sprint 1

    # Then
    The test plans list should contain Sprint 1

Deleting a plan drops it from the plans list
    # Given
    I open the test plans page
    I create a test plan via the UI titled Doomed Plan

    # When
    I delete the test plan Doomed Plan via the UI

    # Then
    The test plans list should not contain Doomed Plan

Multiple plans coexist in the list
    # Given
    I open the test plans page

    # When
    I create a test plan via the UI titled Sprint 2
    I create a test plan via the UI titled Sprint 3

    # Then
    The test plans list should contain Sprint 2
    The test plans list should contain Sprint 3
