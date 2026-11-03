*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I sign in to the UI as ${ADMIN_USER} with password ${ADMIN_PASS}
Suite Teardown    I tear down the frontend suite
Test Teardown     I purge users with prefix ui-reset-


*** Variables ***
${ADMIN_USER}      %{TESTJAM_USER=admin}
${ADMIN_PASS}      %{TESTJAM_PASS=admin123}
${TARGET_USER}     ui-reset-carol
${TARGET_EMAIL}    ui-reset-carol@test.com


*** Test Cases ***
A forgotten password can be replaced through the emailed link
    # Given
    I am authenticated as admin
    I create a user named ${TARGET_USER} with password original-pw1
    I purge emails to ${TARGET_EMAIL}

    # When
    I request a password reset for ${TARGET_EMAIL} via the UI
    I follow the reset link sent to ${TARGET_EMAIL} and choose replaced-pw1

    # Then
    I switch the UI session to ${TARGET_USER} with password replaced-pw1
    I should land on the projects page
