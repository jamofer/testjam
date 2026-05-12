*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I sign in to the UI as ${ADMIN_USER} with password ${ADMIN_PASS}
Suite Teardown    I tear down the frontend suite
Test Setup        Settings are reset to defaults


*** Variables ***
${ADMIN_USER}      %{TESTJAM_USER=admin}
${ADMIN_PASS}      %{TESTJAM_PASS=admin123}


*** Test Cases ***
Saving SMTP host marks the public settings as configured
    # Given
    I open the settings page

    # When
    I fill the SMTP form with host smtp.example.com port 587 from qa@example.com
    I save the settings form

    # Then
    The public settings should report SMTP as configured

Saving the log flush interval persists across a page reload
    # Given
    I open the settings page

    # When
    I set the log flush interval to 250 via the UI
    I save the settings form
    I open the settings page

    # Then
    The log flush interval input should read 250
    The admin settings log flush interval should be 250 milliseconds
