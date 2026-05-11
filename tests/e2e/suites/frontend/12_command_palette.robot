*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I sign in to the UI as ${ADMIN_USER} with password ${ADMIN_PASS}
Suite Teardown    I tear down the frontend suite
Test Setup        I have a fresh project named ${PROJECT_NAME}


*** Variables ***
${ADMIN_USER}      %{TESTJAM_USER=admin}
${ADMIN_PASS}      %{TESTJAM_PASS=admin123}
${PROJECT_NAME}    UI-Palette-Project


*** Test Cases ***
Ctrl+K opens the command palette
    # When
    I open the command palette via keyboard

    # Then
    The palette should list ${PROJECT_NAME}

The sidebar search button also opens the palette
    # When
    I open the command palette via the sidebar

    # Then
    The palette should list ${PROJECT_NAME}

Searching by name narrows the palette results
    # Given
    I open the command palette via keyboard

    # When
    I search the palette for Go to versions

    # Then
    The palette should list Go to versions

A query with no matches shows an empty state
    # Given
    I open the command palette via keyboard

    # When
    I search the palette for zzz-no-such-thing-zzz

    # Then
    The palette should report no matches

Escape closes the command palette
    # Given
    I open the command palette via keyboard

    # When
    I dismiss the command palette

    # Then
    The current url should contain /projects
