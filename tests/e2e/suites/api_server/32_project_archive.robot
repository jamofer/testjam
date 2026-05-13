*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Setup       Fresh project for archive tests
Test Teardown    I purge projects with prefix Arch-


*** Variables ***
${PROJECT_NAME}    Arch-Target


*** Test Cases ***
Archive marks the project and removes it from default listing
    # When
    I archive the project

    # Then
    The response status should be 200
    The project should be archived

Archived project rejects new suites
    # Given
    I archive the project

    # When
    I try to create a suite named NewOne

    # Then
    The response status should be 409

Unarchive restores writability
    # Given
    I archive the project
    I unarchive the project

    # When
    I try to create a suite named NewOne

    # Then
    The response status should be 201


*** Keywords ***
Fresh project for archive tests
    I am authenticated as admin
    I create a project named ${PROJECT_NAME}
