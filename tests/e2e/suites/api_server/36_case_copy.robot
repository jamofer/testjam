*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    I clean up the current project


*** Test Cases ***
Copying a test case adds it to the target suite
    # Given
    I am authenticated as admin
    I create a project named Case-Copy
    I create a suite named archive
    I create a suite named main
    I create a test case named checkout

    # When
    I copy the test case into the suite archive

    # Then
    The suite archive should contain cases checkout
    The suite main should contain cases checkout

Bulk copying a suite's cases creates a new suite with all of them
    # Given
    I am authenticated as admin
    I create a project named Case-Bulk-Copy
    I create a suite named main
    I create a test case named login
    I create a test case named logout

    # When
    I bulk copy the cases of the current suite into a new suite named main-copy

    # Then
    The suite main-copy should contain cases login, logout
