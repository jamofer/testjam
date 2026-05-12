*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I sign in to the UI as ${ADMIN_USER} with password ${ADMIN_PASS}
Suite Teardown    I tear down the frontend suite
Test Setup        I log in as ${ADMIN_USER} with password ${ADMIN_PASS}


*** Variables ***
${ADMIN_USER}      %{TESTJAM_USER=admin}
${ADMIN_PASS}      %{TESTJAM_PASS=admin123}


*** Test Cases ***
A user can change their password from the Profile page
    # Given
    I ensure user profile-pwd has password old-pass99
    I switch the UI session to profile-pwd with password old-pass99
    I open the profile page

    # When
    I change my password from old-pass99 to fresh-pass99 via the UI

    # Then
    I switch the UI session to profile-pwd with password fresh-pass99
    I should land on the projects page

A user can mint a personal token from the Profile page
    # Given
    I create a user named profile-token with password pw12345678
    I switch the UI session to profile-token with password pw12345678
    I open the profile page

    # When
    I create a personal token named ci-bot via the UI

    # Then
    The personal tokens table should list ci-bot

Toggling an email preference persists the new state
    # Given
    I configure SMTP host mailpit port 1025 from qa@example.com
    I create a user named profile-pref with password pw12345678
    I switch the UI session to profile-pref with password pw12345678
    I open the profile page

    # When
    I toggle the email preference for Execution assigned to you

    # Then
    The email preference for Execution assigned to you should be disabled

The SMTP not-configured banner is shown when SMTP is unset
    # Given
    Settings are reset to defaults
    I create a user named profile-banner with password pw12345678
    I switch the UI session to profile-banner with password pw12345678

    # When
    I open the profile page

    # Then
    The SMTP not-configured banner should be visible
