*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    I clean up the current project


*** Test Cases ***
The listener bootstraps a project and reports a completed execution
    # Given
    I am authenticated as admin
    I configure the listener to target project Listener-Smoke

    # When
    I run the listener against fixture fixtures/listener_sample

    # Then
    The listener project should have 1 executions
    The latest listener execution should be completed

The listener reports per-case statuses matching the suite outcome
    # Given
    I am authenticated as admin
    I configure the listener to target project Listener-Statuses

    # When
    I run the listener against fixture fixtures/listener_sample

    # Then
    The latest listener execution should have 3 results
    The latest listener execution should have a passed result for case Successful smoke check
    The latest listener execution should have a failed result for case Failing smoke check

The listener streams step results with captured log output
    # Given
    I am authenticated as admin
    I configure the listener to target project Listener-Logs

    # When
    I run the listener against fixture fixtures/listener_sample

    # Then
    The latest listener execution should have at least one step result
    The latest listener execution should have step result logs containing typing the username
