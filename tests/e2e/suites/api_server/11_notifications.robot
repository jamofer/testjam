*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Setup    Admin notifications are drained
Test Teardown    I clean up the current project


*** Variables ***
${ADMIN_USER}    %{TESTJAM_USER=admin}


*** Test Cases ***
Assigning an execution creates a notification for the assignee
    # Given
    I am authenticated as admin
    I create a project named Notifications-Assign
    I create a user named bob with password bob123
    The inbox of bob is drained with password bob123

    # When
    I start an execution titled Sprint 1 assigned to bob

    # Then
    I log in as bob with password bob123
    I have 1 unread notifications
    The latest notification should be of type execution_assigned
    The latest notification message should contain Sprint 1

Unread count reflects new notifications
    # Given
    I am authenticated as admin
    I create a project named Notifications-Unread
    I create a user named carol with password carol123
    The inbox of carol is drained with password carol123

    # When
    I start an execution titled Run A assigned to carol
    I start an execution titled Run B assigned to carol

    # Then
    I log in as carol with password carol123
    I have 2 unread notifications

Marking a notification as read decrements the unread count
    # Given
    I am authenticated as admin
    I create a project named Notifications-MarkOne
    I create a user named dave with password dave123
    The inbox of dave is drained with password dave123
    I start an execution titled Run X assigned to dave
    I start an execution titled Run Y assigned to dave
    I log in as dave with password dave123

    # When
    I mark the latest notification as read

    # Then
    I have 1 unread notifications

Marking all notifications as read empties the unread count
    # Given
    I am authenticated as admin
    I create a project named Notifications-MarkAll
    I create a user named eve with password eve123
    The inbox of eve is drained with password eve123
    I start an execution titled Run M assigned to eve
    I start an execution titled Run N assigned to eve
    I log in as eve with password eve123

    # When
    I mark all notifications as read

    # Then
    I have 0 unread notifications

Notifications are isolated per user
    # Given
    I am authenticated as admin
    I create a project named Notifications-Isolation
    I create a user named frank with password frank123
    The inbox of frank is drained with password frank123
    I start an execution titled For Frank assigned to frank

    # When
    I log in as frank with password frank123

    # Then
    I have 1 unread notifications

    # And
    I am authenticated as admin
    I have 0 unread notifications

Assigning an execution to the creator does not produce a notification
    # Given
    I am authenticated as admin
    I create a project named Notifications-SelfAssign

    # When
    I start an execution titled My own run assigned to ${ADMIN_USER}

    # Then
    I have 0 unread notifications
