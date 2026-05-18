*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    I clean up the current project


*** Variables ***
${ADMIN_USER}    %{TESTJAM_USER=admin}
${ADMIN_PASS}    %{TESTJAM_PASS=admin123}
${BOB_EMAIL}     bob@test.com


*** Test Cases ***
Assigning an execution sends an email to the assignee
    # Given
    I am authenticated as admin
    I create a project named Emails-Assign
    I create a user named bob with password bob123
    I purge emails to ${BOB_EMAIL}

    # When
    I start an execution titled Sprint 1 assigned to bob

    # Then
    I wait for 1 emails to ${BOB_EMAIL}
    The latest email to ${BOB_EMAIL} subject should contain assigned to

Completing a failing execution emails creator and assignee
    # Given
    I am authenticated as admin
    ${admin_email}=    The current user email
    I create a project named Emails-Failed
    I create a user named bob with password bob123
    I create a suite named main
    I create a test case named case_a
    I start an execution titled Failing run for the current suite
    I assign the execution to bob
    I purge emails to ${BOB_EMAIL}
    I purge emails to ${admin_email}
    I bulk report all results in the current execution as failed

    # When
    I complete the execution

    # Then
    I wait for 1 emails to ${BOB_EMAIL} within 3 seconds
    I wait for 1 emails to ${admin_email} within 3 seconds
