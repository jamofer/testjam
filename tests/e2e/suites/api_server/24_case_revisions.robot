*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    I clean up the current project


*** Test Cases ***
Creating a test case writes a creation revision
    # Given
    I am authenticated as admin
    I create a project named Case-Revisions-Create
    I create a suite named main

    # When
    I create a test case named newborn

    # Then
    The test case should have 1 revisions
    The latest revision change kind should be created

Editing a test case writes a new updated revision
    # Given
    I am authenticated as admin
    I create a project named Case-Revisions-Update
    I create a suite named main
    I create a test case named edited

    # When
    I rename the test case to edited-renamed

    # Then
    The test case should have 2 revisions
    The latest revision change kind should be updated
