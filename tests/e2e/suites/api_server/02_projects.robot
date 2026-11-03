*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Test Cases ***
Create and read a project
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    # When
    I create a project named Acme App
    # Then
    The project name should be Acme App

Rename a project
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Old Name
    # When
    I rename the project to New Name
    # Then
    The project name should be New Name

Delete a project
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named To Be Deleted
    # When
    I delete the project
    # Then
    The project should no longer exist
