*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    I clean up the current project


*** Test Cases ***
Bulk reporting all cases updates the existing not-run results
    # Given
    I am authenticated as admin
    I create a project named Bulk-Update
    I create a suite named main
    I create a test case named case_a
    I create a test case named case_b
    I create a test case named case_c
    I start an execution titled Bulk run for the current suite

    # When
    I bulk report all results in the current execution as passed

    # Then
    The bulk response should have 0 created and 3 updated
    The bulk response should have 0 errors

Re-bulk reporting the same cases keeps the updated counter incrementing
    # Given
    I am authenticated as admin
    I create a project named Bulk-Rerun
    I create a suite named main
    I create a test case named case_a
    I create a test case named case_b
    I start an execution titled Run for the current suite
    I bulk report all results in the current execution as passed

    # When
    I bulk report all results in the current execution as failed

    # Then
    The bulk response should have 0 created and 2 updated
    The bulk response should have 0 errors

Bulk reporting respects the supplied status per item
    # Given
    I am authenticated as admin
    I create a project named Bulk-Statuses
    I create a suite named main
    I create a test case named case_a
    I create a test case named case_b
    I start an execution titled Run for the current suite

    # When
    I bulk report all results in the current execution as blocked

    # Then
    The bulk response should have 0 created and 2 updated
    The bulk response should have 0 errors
