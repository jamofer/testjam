*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Test Cases ***
Create and read a version
    [Teardown]    I clean up the current project
    # Given a project
    I am authenticated as admin
    I create a project named Versioned App
    # When I create a version
    I create version 1.0.0
    # Then the version is active by default
    The version status should be active

Release a version
    [Teardown]    I clean up the current project
    # Given an active version
    I am authenticated as admin
    I create a project named Release App
    I create version 2.0.0
    # When I release it
    I release the version
    # Then the status is released
    The version status should be released

Archive a version
    [Teardown]    I clean up the current project
    # Given a released version
    I am authenticated as admin
    I create a project named Archive App
    I create version 3.0.0
    I release the version
    # When I archive it
    I archive the version
    # Then the status is archived
    The version status should be archived

Delete a version
    [Teardown]    I clean up the current project
    # Given an active version
    I am authenticated as admin
    I create a project named Delete Version App
    I create version 0.1.0
    # When I delete it
    I delete the version
    # Then it is gone
    The version should no longer exist

Project accumulates multiple versions
    [Teardown]    I clean up the current project
    # Given a project
    I am authenticated as admin
    I create a project named Multi Version App
    # When I create three versions
    I create version 1.0.0
    I create version 2.0.0
    I create version 3.0.0
    # Then all three are listed
    The project should have 3 versions

Execution linked to a version
    [Teardown]    I clean up the current project
    # Given a project with a version
    I am authenticated as admin
    I create a project named Linked App
    I create version v1.2.3
    # When I create an execution for that version
    I start a versioned execution titled Regression Run
    # Then the execution references the version
    The execution version should be set

Version with VCS tag
    [Teardown]    I clean up the current project
    # Given a project
    I am authenticated as admin
    I create a project named Tagged App
    # When I create a version with a git tag
    I create version 1.0.0 tagged v1.0.0
    # Then the version is stored as active
    The version status should be active
