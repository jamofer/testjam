*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    I clean up the current project


*** Test Cases ***
The coverage matrix shows the latest result per version
    # Given
    I am authenticated as admin
    I create a project named Coverage-Latest
    I create a suite named main
    I create a test case named checkout
    I create version 1.0
    I create version 2.0

    # When
    I record a passed result for the test case in version 1.0
    I record a failed result for the test case in version 2.0

    # Then
    The coverage of the test case in version 1.0 should be passed
    The coverage of the test case in version 2.0 should be failed

A version without runs leaves the case uncovered
    # Given
    I am authenticated as admin
    I create a project named Coverage-Empty
    I create a suite named main
    I create a test case named refund
    I create version 1.0

    # When
    I create version 2.0

    # Then
    The coverage matrix should list versions 1.0, 2.0
    The test case should have no coverage in version 2.0

Archived versions drop out of the matrix
    # Given
    I am authenticated as admin
    I create a project named Coverage-Archived
    I create a suite named main
    I create a test case named login
    I create version 1.0
    I create version 2.0

    # When
    I archive the version

    # Then
    The coverage matrix should list versions 1.0
