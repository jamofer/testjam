*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I sign in to the UI as ${ADMIN_USER} with password ${ADMIN_PASS}
Suite Teardown    I tear down the frontend suite
Test Teardown     I purge users with prefix ui-locale-


*** Variables ***
${ADMIN_USER}      %{TESTJAM_USER=admin}
${ADMIN_PASS}      %{TESTJAM_PASS=admin123}
${LOCALE_USER}     ui-locale-dana


*** Test Cases ***
Switching the language to Spanish translates the app and is saved
    # Given
    I am authenticated as admin
    I create a user named ${LOCALE_USER} with password locale-pw1
    I switch the UI session to ${LOCALE_USER} with password locale-pw1
    I open the profile page

    # When
    I switch the interface language to Spanish via the UI

    # Then
    The sidebar should offer Proyectos
    I log in as ${LOCALE_USER} with password locale-pw1
    My saved language should be es
