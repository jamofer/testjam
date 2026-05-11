*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Setup    The email pipeline is reset
Test Teardown    I clean up the current project


*** Variables ***
${ADMIN_USER}    %{TESTJAM_USER=admin}


*** Test Cases ***
Assigning an execution sends an email to the assignee
    # Given
    I am authenticated as admin
    I configure SMTP to use mailpit
    I create a project named Emails-Assign
    I create a user named bob with password bob123

    # When
    I start an execution titled Sprint 1 assigned to bob

    # Then
    I wait for 1 emails in the mailbox
    The latest email recipient should be bob@test.com
    The latest email subject should contain assigned to

Self-assigning does not send an email
    # Given
    I am authenticated as admin
    I configure SMTP to use mailpit
    I create a project named Emails-Self

    # When
    I start an execution titled My own run assigned to ${ADMIN_USER}

    # Then
    The mailbox should be empty

Completing a failing execution emails creator and assignee
    # Given
    I am authenticated as admin
    I configure SMTP to use mailpit
    I create a project named Emails-Failed
    I create a user named bob with password bob123
    I create a suite named main
    I create a test case named case_a
    I start an execution titled Failing run for the current suite
    I assign the execution to bob
    The mailbox is purged
    I bulk report all results in the current execution as failed

    # When
    I complete the execution

    # Then
    I wait for 2 emails in the mailbox within 3 seconds
    The mailbox should contain an email to bob@test.com

Disabling the email preference suppresses the dispatch
    # Given
    I am authenticated as admin
    I configure SMTP to use mailpit
    I disable email notifications for execution_assigned
    I create a project named Emails-Pref
    I create a user named carol with password carol123
    I disable email notifications for execution_assigned

    # When
    I start an execution titled With pref off assigned to carol

    # Then
    The mailbox should be empty

SMTP unconfigured leaves the mailbox empty
    # Given
    I am authenticated as admin
    I create a project named Emails-NoSmtp
    I create a user named dave with password dave123

    # When
    I start an execution titled No SMTP assigned to dave

    # Then
    The mailbox should be empty
