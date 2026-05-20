*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Test Cases ***
Create a custom field and filter bugs by value
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Custom Fields App
    I create a priority custom field for bugs

    # When
    I create a bug titled Login crash with priority p0
    I create a bug titled Typo in footer with priority p1

    # Then
    The bug list filtered by priority p0 should have 1 entries
    The bug list filtered by priority p1 should have 1 entries
