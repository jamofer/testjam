*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Test Cases ***
Create and complete an execution
    [Teardown]    I clean up the current project
    # Given a project with a test case
    I am authenticated as admin
    I create a project named Exec Project
    I create a suite named Exec Suite
    ${case_id}=    I create a test case named Login Test
    # When I start an execution and report a result
    I start an execution titled Sprint 1 Run
    I report case ${case_id} as passed
    I complete the execution
    # Then the execution is in completed state
    The execution status should be completed

Execution tracks result count
    [Teardown]    I clean up the current project
    # Given a project with two test cases
    I am authenticated as admin
    I create a project named Result Count Project
    I create a suite named Result Count Suite
    ${case_a}=    I create a test case named Test A
    ${case_b}=    I create a test case named Test B
    # When I report results for both cases
    I start an execution titled Count Check Run
    I report case ${case_a} as passed
    I report case ${case_b} as failed
    # Then two results exist
    The execution should have 2 results

Abort an execution
    [Teardown]    I clean up the current project
    # Given a running execution
    I am authenticated as admin
    I create a project named Abort Project
    I start an execution titled Run To Abort
    # When I abort it
    I abort the execution
    # Then the status reflects the abort
    The execution status should be aborted

Delete an execution
    [Teardown]    I clean up the current project
    # Given a completed execution
    I am authenticated as admin
    I create a project named Cleanup Project
    I start an execution titled To Delete
    I complete the execution
    # When I delete it
    I delete the execution
    # Then it is gone
    The execution should no longer exist
