*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    I clean up the current project


*** Test Cases ***
Reordering steps reflects the new sequence
    # Given
    I am authenticated as admin
    I create a project named Case-Reorder
    I create a suite named main
    I create a test case named flow
    I add a step Open page to the test case
    I add a step Fill form to the test case
    I add a step Submit to the test case

    # When
    I reorder the steps to Submit, Open page, Fill form

    # Then
    The test case steps should be ordered as Submit, Open page, Fill form
