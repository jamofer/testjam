*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    I clean up the current project


*** Test Cases ***
Starting a step result persists running state
    # Given
    I have a live-ready execution with one step Open the page

    # When
    I start a step result for step Open the page

    # Then
    The current step result should be in running state
    The current step result should have a start timestamp

Starting a step result twice for the same step does not duplicate
    # Given
    I have a live-ready execution with one step Click login
    I start a step result for step Click login

    # When
    I start a step result for step Click login

    # Then
    The current result should have 1 step results
    The current step result should be in running state

Appending log lines accumulates them with a blank line separator
    # Given
    I have a live-ready execution with one step Run something
    I start a step result for step Run something

    # When
    I append a INFO log line started
    I append a INFO log line in progress
    I append a FAIL log line boom

    # Then
    The current step result log should have 3 entries
    The current step result log should contain started
    The current step result log should contain boom

Finishing a step result records status and duration
    # Given
    I have a live-ready execution with one step Click here
    I start a step result for step Click here

    # When
    I finish the current step result with status passed duration 1234 ms

    # Then
    The current step result should be in passed state
    The current step result should have duration 1234 ms
