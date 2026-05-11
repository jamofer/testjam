*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I sign in to the UI as ${ADMIN_USER} with password ${ADMIN_PASS}
Suite Teardown    I tear down the frontend suite
Test Setup        The projects page is fresh with no UI-Project- projects


*** Variables ***
${ADMIN_USER}    %{TESTJAM_USER=admin}
${ADMIN_PASS}    %{TESTJAM_PASS=admin123}


*** Test Cases ***
Creating a project shows it in the list
    # When
    I create a project via the UI named UI-Project-Alpha

    # Then
    The projects list should contain UI-Project-Alpha

Deleting a project drops it from the list
    # Given
    I create a project via the UI named UI-Project-Doomed

    # When
    I delete the project UI-Project-Doomed via the UI

    # Then
    The projects list should not contain UI-Project-Doomed

Searching by name filters the list
    # Given
    I create a project via the UI named UI-Project-Bravo
    I create a project via the UI named UI-Project-Charlie

    # When
    I search projects for Charlie

    # Then
    The projects list should contain UI-Project-Charlie
    The projects list should not contain UI-Project-Bravo
