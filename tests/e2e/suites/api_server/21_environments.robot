*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Test Cases ***
Create an environment catalog entry
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Env Catalog App

    # When
    I create environment Production with slug production

    # Then
    The project should have 1 environments

Mark an environment as default
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Default Env App
    I create environment Staging with slug staging
    I create environment Production with slug production

    # When
    I mark the environment as default

    # Then
    The environment should be the default

Archive an environment instead of deleting it
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Archive Env App
    I create environment Production with slug production
    I start an execution targeting environment production

    # When
    I delete the environment
    The response status should be 409
    I archive the environment

    # Then
    The environment should be archived

Execution auto-creates an environment entry
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Auto Env App

    # When
    I start an execution targeting environment qa-cell

    # Then
    The project should have 1 environments
