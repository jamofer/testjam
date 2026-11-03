*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Variables ***
${ADMIN_USER}    %{TESTJAM_USER=admin}


*** Test Cases ***
Create and use a user token
    [Teardown]    The admin personal tokens are cleaned up
    # Given
    I am authenticated as admin
    ${token}=    I create a user token named CI Pipeline

    # When
    I authenticate using token ${token}

    # Then
    The current user should be ${ADMIN_USER}

User token is listed with prefix only
    [Teardown]    The admin personal tokens are cleaned up
    # Given
    I am authenticated as admin

    # When
    I create a user token named Listed Token

    # Then
    My user token Listed Token should be listed by prefix only

Create and use a project token
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Project Token Project
    ${token}=    I create a project token named Listener

    # When
    the project should have 1 api tokens
    I authenticate using token ${token}

    # Then
    The current user should be ${ADMIN_USER}

Revoke a project token blocks further access
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Revoke Token Project
    I create a project token named Temp Token
    the project should have 1 api tokens

    # When
    I revoke the project token named Temp Token

    # Then
    the project should have 0 api tokens

Non-owner cannot create project token
    [Teardown]    I clean up the current project
    # Given
    I am authenticated as admin
    I create a project named Protected Token Project
    I create a user named nontokenuser with password pw123
    I log in as nontokenuser with password pw123

    # When
    I try to create a project token named Forbidden

    # Then
    The response status should be 403
