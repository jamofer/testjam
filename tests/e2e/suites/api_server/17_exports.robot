*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    I clean up the current project


*** Test Cases ***
The HTML report download returns HTML content
    # Given
    I have a live-ready execution with one step Login

    # When
    I download the HTML report for the execution

    # Then
    The downloaded HTML report content type should be html
    The downloaded HTML report should not be empty

The HTML report mentions the execution title
    # Given
    I am authenticated as admin
    I create a project named Reports
    I create a suite named main
    I create a test case named smoke_login
    I start an execution titled Smoke run for the current suite

    # When
    I download the HTML report for the execution

    # Then
    The downloaded HTML report should contain Smoke run
    The downloaded HTML report should contain smoke_login

The HTML report reflects the reported case status
    # Given
    I am authenticated as admin
    I create a project named Reports-Status
    I create a suite named main
    I create a test case named flaky_check
    I start an execution titled Status run for the current suite
    I select the result for the current case
    I bulk report all results in the current execution as failed

    # When
    I download the HTML report for the execution

    # Then
    The downloaded HTML report should contain flaky_check
    The downloaded HTML report should contain failed
