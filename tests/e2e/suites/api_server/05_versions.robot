*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Test Cases ***
Create and read a version
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Versioned App
    # When
    I create version 1.0.0
    # Then
    The version status should be active

Release a version
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Release App
    I create version 2.0.0
    # When
    I release the version
    # Then
    The version status should be released

Archive a version
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Archive App
    I create version 3.0.0
    I release the version
    # When
    I archive the version
    # Then
    The version status should be archived

Delete a version
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Delete Version App
    I create version 0.1.0
    # When
    I delete the version
    # Then
    The version should no longer exist

Project accumulates multiple versions
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Multi Version App
    # When
    I create version 1.0.0
    I create version 2.0.0
    I create version 3.0.0
    # Then
    The project should have 3 versions

Execution linked to a version
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Linked App
    I create version v1.2.3
    # When
    I start a versioned execution titled Regression Run
    # Then
    The execution version should be set

Version with VCS tag
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Tagged App
    # When
    I create version 1.0.0 tagged v1.0.0
    # Then
    The version status should be active
