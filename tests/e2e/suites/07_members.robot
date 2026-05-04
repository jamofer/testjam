*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Test Cases ***
Add and list project members
    [Teardown]    I clean up the current project
    I am authenticated as admin
    I create a project named Member Test Project
    I create a user named tester1 with password pw123
    I add tester1 as tester to the project
    the project should have 2 members
    tester1 should have role tester in the project

Update member role
    [Teardown]    I clean up the current project
    I am authenticated as admin
    I create a project named Role Update Project
    I create a user named roleuser with password pw123
    I add roleuser as viewer to the project
    roleuser should have role viewer in the project
    I update roleuser role to tester
    roleuser should have role tester in the project

Remove member from project
    [Teardown]    I clean up the current project
    I am authenticated as admin
    I create a project named Remove Member Project
    I create a user named removeme with password pw123
    I add removeme as viewer to the project
    the project should have 2 members
    I remove removeme from the project
    the project should have 1 members

Invalid role is rejected
    [Teardown]    I clean up the current project
    I am authenticated as admin
    I create a project named Invalid Role Project
    I create a user named roletest with password pw123
    I try to add roletest as superadmin to the project
    The response status should be 400
