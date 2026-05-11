*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I sign in to the UI as ${ADMIN_USER} with password ${ADMIN_PASS}
Suite Teardown    I tear down the frontend suite
Test Teardown     I switch to desktop viewport


*** Variables ***
${ADMIN_USER}      %{TESTJAM_USER=admin}
${ADMIN_PASS}      %{TESTJAM_PASS=admin123}


*** Test Cases ***
The hamburger button appears on a mobile viewport
    # Given
    I switch to mobile viewport

    # Then
    The mobile menu button should be visible

Tapping the hamburger reveals the sidebar
    # Given
    I switch to mobile viewport

    # When
    I open the mobile sidebar

    # Then
    The mobile sidebar should be open

Tapping the backdrop dismisses the sidebar
    # Given
    I switch to mobile viewport
    I open the mobile sidebar

    # When
    I dismiss the mobile sidebar via the backdrop

    # Then
    The mobile sidebar should be closed
