*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    I clean up the current project


*** Test Cases ***
Uploading a file attaches it to the execution
    # Given
    I have a live-ready execution with one step Run

    # When
    I attach file fixtures/junit_results.xml to the execution

    # Then
    The execution should have 1 attachments
    The execution attachments should contain junit_results.xml

Attaching multiple files accumulates the count
    # Given
    I have a live-ready execution with one step Run

    # When
    I attach file fixtures/junit_results.xml to the execution
    I attach file fixtures/rf_output.xml to the execution

    # Then
    The execution should have 2 attachments

Deleting an attachment removes it from the listing
    # Given
    I have a live-ready execution with one step Run
    I attach file fixtures/junit_results.xml to the execution
    I attach file fixtures/rf_output.xml to the execution

    # When
    I delete the execution attachment named junit_results.xml

    # Then
    The execution should have 1 attachments
    The execution attachments should contain rf_output.xml

Uploading a file attaches it to a specific result
    # Given
    I have a live-ready execution with one step Run

    # When
    I attach file fixtures/junit_results.xml to the current result

    # Then
    The current result should have 1 attachments
