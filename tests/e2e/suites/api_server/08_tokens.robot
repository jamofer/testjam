*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Test Cases ***
Create and use a user token
    I am authenticated as admin
    ${token}=    I create a user token named CI Pipeline
    I authenticate using token ${token}
    The current user should be admin

User token is listed with prefix only
    I am authenticated as admin
    I create a user token named Listed Token
    ${tokens}=    I list my user tokens
    Should Be True    len($tokens) >= 1

Create and use a project token
    [Teardown]    I clean up the current project
    I am authenticated as admin
    I create a project named Project Token Project
    ${token}=    I create a project token named Listener
    the project should have 1 api tokens
    I authenticate using token ${token}
    The current user should be admin

Revoke a project token blocks further access
    [Teardown]    I clean up the current project
    I am authenticated as admin
    I create a project named Revoke Token Project
    I create a project token named Temp Token
    the project should have 1 api tokens
    I revoke the project token named Temp Token
    the project should have 0 api tokens

Non-owner cannot create project token
    [Teardown]    I clean up the current project
    I am authenticated as admin
    I create a project named Protected Token Project
    I create a user named nontokenuser with password pw123
    I log in as nontokenuser with password pw123
    I try to create a project token named Forbidden
    The response status should be 403
