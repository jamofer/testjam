*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    I clean up the current project


*** Variables ***
${ASSIGNEE}         result-assignee
${OUTSIDER}         result-outsider
${PASSWORD}         pw-assignee


*** Test Cases ***
A tester finds the results assigned to them
    # Given
    I am authenticated as admin
    I create a project named Result-Assignee
    I create a user named ${ASSIGNEE} with password ${PASSWORD}
    I add ${ASSIGNEE} as tester to the project
    I create a suite named main
    ${login}=    I create a test case named login
    ${logout}=    I create a test case named logout
    I start an execution titled Sprint
    I report case ${login} as not_run
    I report case ${logout} as not_run

    # When
    I assign the result of case ${login} to ${ASSIGNEE}

    # Then
    The results assigned to ${ASSIGNEE} should be cases login

Unassigning a result frees it
    # Given
    I am authenticated as admin
    I create a project named Result-Unassign
    I create a user named ${ASSIGNEE} with password ${PASSWORD}
    I add ${ASSIGNEE} as tester to the project
    I create a suite named main
    ${login}=    I create a test case named login
    I start an execution titled Sprint
    I report case ${login} as not_run
    I assign the result of case ${login} to ${ASSIGNEE}

    # When
    I unassign the result of case ${login}

    # Then
    No result should be assigned to ${ASSIGNEE}

Assigning a result to someone outside the project is refused
    # Given
    I am authenticated as admin
    I create a project named Result-Outsider
    I create a user named ${OUTSIDER} with password ${PASSWORD}
    I create a suite named main
    ${login}=    I create a test case named login
    I start an execution titled Sprint
    I report case ${login} as not_run

    # When
    I try to assign the result of case ${login} to ${OUTSIDER}

    # Then
    The response status should be 422

Re-running an execution keeps each result's assignee
    # Given
    I am authenticated as admin
    I create a project named Result-Assignee-Rerun
    I create a user named ${ASSIGNEE} with password ${PASSWORD}
    I add ${ASSIGNEE} as tester to the project
    I create a suite named main
    ${login}=    I create a test case named login
    ${logout}=    I create a test case named logout
    I start an execution titled Sprint
    I report case ${login} as failed
    I report case ${logout} as failed
    I assign the result of case ${logout} to ${ASSIGNEE}
    I complete the execution

    # When
    I re-run every case of the execution

    # Then
    The results assigned to ${ASSIGNEE} should be cases logout
