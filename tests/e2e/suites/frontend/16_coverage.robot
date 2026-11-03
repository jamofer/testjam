*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I sign in to the UI as ${ADMIN_USER} with password ${ADMIN_PASS}
Suite Teardown    I tear down the frontend suite
Test Setup        I have a fresh project named ${PROJECT_NAME}


*** Variables ***
${ADMIN_USER}      %{TESTJAM_USER=admin}
${ADMIN_PASS}      %{TESTJAM_PASS=admin123}
${PROJECT_NAME}    UI-Coverage-Project


*** Test Cases ***
The coverage page shows each version's latest result
    # Given
    I create a suite named Checkout
    I create a test case named Pay by card
    I create version 1.0
    I create version 2.0
    I record a passed result for the test case in version 1.0
    I record a failed result for the test case in version 2.0

    # When
    I open the coverage page

    # Then
    The coverage cell of the test case in version 1.0 should show passed
    The coverage cell of the test case in version 2.0 should show failed
