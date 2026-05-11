*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I sign in to the UI as ${ADMIN_USER} with password ${ADMIN_PASS}
Suite Teardown    I tear down the frontend suite
Test Setup        I have a fresh manual run with one stepped case


*** Variables ***
${ADMIN_USER}      %{TESTJAM_USER=admin}
${ADMIN_PASS}      %{TESTJAM_PASS=admin123}


*** Test Cases ***
The live indicator appears once the WebSocket connects
    # When
    I open the run page for the current execution

    # Then
    The live indicator should be visible

A backend step_result.started event opens the log panel on the running step
    # Given
    I open the run page for the current execution
    I expand the result card for case Smoke flow

    # When
    I trigger a backend step_result.started for the current execution
    I append a backend log Boot complete to the running step

    # Then
    The step 1 log panel should contain Boot complete

Streaming logs appear in the panel without a page reload
    # Given
    I open the run page for the current execution
    I expand the result card for case Smoke flow
    I trigger a backend step_result.started for the current execution

    # When
    I append a backend log first line to the running step
    I append a backend log second line to the running step

    # Then
    The step 1 log panel should contain first line
    The step 1 log panel should contain second line
