*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I sign in to the UI as ${ADMIN_USER} with password ${ADMIN_PASS}
Suite Teardown    I tear down the frontend suite
Test Setup        I have a fresh project named ${PROJECT_NAME} with three suites


*** Variables ***
${ADMIN_USER}      %{TESTJAM_USER=admin}
${ADMIN_PASS}      %{TESTJAM_PASS=admin123}
${PROJECT_NAME}    UI-Tree-Project


*** Test Cases ***
Pressing right arrow on a collapsed suite expands it
    # Given
    I focus the suite Alpha
    I press shortcut ArrowLeft

    # When
    I press shortcut ArrowRight

    # Then
    The suite Alpha should be expanded

Pressing left arrow on an expanded suite collapses it
    # Given
    I focus the suite Alpha

    # When
    I press shortcut ArrowLeft

    # Then
    The suite Alpha should be collapsed

Arrow down moves focus to the next suite
    # Given
    I focus the suite Alpha

    # When
    I press shortcut ArrowDown

    # Then
    The suite Beta should be focused

Arrow up moves focus to the previous suite
    # Given
    I focus the suite Beta

    # When
    I press shortcut ArrowUp

    # Then
    The suite Alpha should be focused
