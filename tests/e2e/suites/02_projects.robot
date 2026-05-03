*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Test Cases ***
Create and read a project
    [Teardown]    I clean up the current project
    # Given an authenticated session
    I am authenticated as admin
    # When I create a project
    I create a project named Acme App
    # Then the name is stored correctly
    The project name should be Acme App

Rename a project
    [Teardown]    I clean up the current project
    # Given an existing project
    I am authenticated as admin
    I create a project named Old Name
    # When I rename it
    I rename the project to New Name
    # Then the updated name is returned
    The project name should be New Name

Delete a project
    [Teardown]    I clean up the current project
    # Given an existing project
    I am authenticated as admin
    I create a project named To Be Deleted
    # When I delete it
    I delete the project
    # Then the project is gone
    The project should no longer exist
