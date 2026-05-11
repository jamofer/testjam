*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I sign in to the UI as ${ADMIN_USER} with password ${ADMIN_PASS}
Suite Teardown    I tear down the frontend suite
Test Setup        I have a fresh project named ${PROJECT_NAME}


*** Variables ***
${ADMIN_USER}      %{TESTJAM_USER=admin}
${ADMIN_PASS}      %{TESTJAM_PASS=admin123}
${PROJECT_NAME}    UI-SuitesCases-Project


*** Test Cases ***
Creating a suite shows it in the project detail
    # When
    I create a suite via the UI named Smoke

    # Then
    The project should list the suite Smoke

Deleting a suite drops it from the project detail
    # Given
    I create a suite via the UI named Doomed

    # When
    I delete the suite Doomed via the UI

    # Then
    The project should not list the suite Doomed

Adding a test case under a suite shows it in the suite
    # Given
    I create a suite via the UI named Auth

    # When
    I add a test case via the UI named login_smoke under the suite Auth

    # Then
    The suite should list the test case login_smoke

Deleting a test case drops it from the suite
    # Given
    I create a suite via the UI named Profile
    I add a test case via the UI named change_password under the suite Profile

    # When
    I delete the test case change_password via the UI

    # Then
    The suite should not list the test case change_password
