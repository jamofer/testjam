*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    I clean up the current project


*** Test Cases ***
Re-running the cases that did not pass skips the passed ones
    # Given
    I am authenticated as admin
    I create a project named Rerun-Not-Passed
    I create a suite named main
    ${login}=    I create a test case named login
    ${logout}=    I create a test case named logout
    ${search}=    I create a test case named search
    I start an execution titled Nightly
    I report case ${login} as passed
    I report case ${logout} as failed
    I report case ${search} as blocked
    I complete the execution

    # When
    I re-run the cases of the execution that did not pass

    # Then
    The execution should be titled Nightly
    The execution should cover cases logout, search
    Every result of the execution should be not_run

Re-running every case covers the whole execution
    # Given
    I am authenticated as admin
    I create a project named Rerun-All
    I create a suite named main
    ${login}=    I create a test case named login
    ${logout}=    I create a test case named logout
    I start an execution titled Nightly
    I report case ${login} as passed
    I report case ${logout} as failed
    I complete the execution

    # When
    I re-run every case of the execution

    # Then
    The execution should cover cases login, logout
    Every result of the execution should be not_run

Re-running the failures of a fully passed execution is refused
    # Given
    I am authenticated as admin
    I create a project named Rerun-Nothing-Left
    I create a suite named main
    ${login}=    I create a test case named login
    I start an execution titled Nightly
    I report case ${login} as passed
    I complete the execution

    # When
    I try to re-run the cases of the execution that did not pass

    # Then
    The response status should be 409
