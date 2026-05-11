*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I sign in to the UI as ${ADMIN_USER} with password ${ADMIN_PASS}
Suite Teardown    I tear down the frontend suite
Test Setup        I have a fresh manual run with three cases


*** Variables ***
${ADMIN_USER}      %{TESTJAM_USER=admin}
${ADMIN_PASS}      %{TESTJAM_PASS=admin123}
${PROJECT_NAME}    UI-Run-Project


*** Test Cases ***
Opening the run page focuses the first result
    # When
    I open the run page for the current execution

    # Then
    The focused result should be the first in the list
    The focused result status should be not_run

Pressing j moves focus to the next result
    # Given
    I open the run page for the current execution

    # When
    I press shortcut j

    # Then
    The focused result should be the second in the list

Pressing k moves focus back to the previous result
    # Given
    I open the run page for the current execution
    I press shortcut j
    I press shortcut j

    # When
    I press shortcut k

    # Then
    The focused result should be the second in the list

Marking results with shortcuts updates the run summary
    # Given
    I open the run page for the current execution

    # When
    I mark the focused result as passed
    I press shortcut j
    I mark the focused result as failed
    I press shortcut j
    I mark the focused result as blocked

    # Then
    The run summary should be passed 1 failed 1 blocked 1

Finishing the execution flips the status badge to completed
    # Given
    I open the run page for the current execution
    I mark the focused result as passed
    I press shortcut j
    I mark the focused result as passed
    I press shortcut j
    I mark the focused result as passed

    # When
    I finish the execution via the UI

    # Then
    The execution status should be completed
