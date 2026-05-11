*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I sign in to the UI as ${ADMIN_USER} with password ${ADMIN_PASS}
Suite Teardown    I tear down the frontend suite
Test Setup        I have a fresh project named ${PROJECT_NAME}


*** Variables ***
${ADMIN_USER}      %{TESTJAM_USER=admin}
${ADMIN_PASS}      %{TESTJAM_PASS=admin123}
${PROJECT_NAME}    UI-Versions-Project


*** Test Cases ***
Creating a version shows it in the versions list
    # Given
    I open the versions page

    # When
    I create a version via the UI named 1.0.0

    # Then
    The versions list should contain 1.0.0

Creating a version with a VCS tag persists it
    # Given
    I open the versions page

    # When
    I create a version via the UI named 1.1.0 tagged v1.1.0

    # Then
    The versions list should contain 1.1.0
    The version 1.1.0 should have tag v1.1.0

Deleting a version drops it from the list
    # Given
    I open the versions page
    I create a version via the UI named doomed

    # When
    I delete the version doomed via the UI

    # Then
    The versions list should not contain doomed

Cycling a version status moves it through the lifecycle
    # Given
    I open the versions page
    I create a version via the UI named lifecycle

    # When
    I cycle the status of version lifecycle

    # Then
    The version lifecycle should be in released state
