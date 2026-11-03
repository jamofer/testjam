*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I sign in to the UI as ${ADMIN_USER} with password ${ADMIN_PASS}
Suite Teardown    I tear down the frontend suite
Test Setup        I have a fresh project named ${PROJECT_NAME}


*** Variables ***
${ADMIN_USER}      %{TESTJAM_USER=admin}
${ADMIN_PASS}      %{TESTJAM_PASS=admin123}
${PROJECT_NAME}    UI-New-Execution-Project


*** Test Cases ***
Starting a run from the form opens it with the picked cases
    # Given
    I create a suite named Checkout
    I create a test case named Pay by card
    I create a test case named Pay by transfer
    I open the new execution page

    # When
    I start a run titled Release candidate with every case of the suite Checkout via the UI

    # Then
    The run page should list 2 results
