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
    I create a user named inbox-bob with password bob123
    The inbox of inbox-bob is drained with password bob123

    # When
    I start an execution titled Sprint 1 assigned to inbox-bob

    # Then
    I log in as inbox-bob with password bob123
    I have 1 unread notifications
    The latest notification should be of type execution_assigned
    The latest notification message should contain Sprint 1

Unread count reflects new notifications
    # Given
    I am authenticated as admin
    I create a project named Notifications-Unread
    I create a user named inbox-carol with password carol123
    The inbox of inbox-carol is drained with password carol123

    # When
    I start an execution titled Run A assigned to inbox-carol
    I start an execution titled Run B assigned to inbox-carol

    # Then
    I log in as inbox-carol with password carol123
    I have 2 unread notifications

Marking a notification as read decrements the unread count
    # Given
    I am authenticated as admin
    I create a project named Notifications-MarkOne
    I create a user named inbox-dave with password dave123
    The inbox of inbox-dave is drained with password dave123
    I start an execution titled Run X assigned to inbox-dave
    I start an execution titled Run Y assigned to inbox-dave
    I log in as inbox-dave with password dave123

    # When
    I mark the latest notification as read

    # Then
    I have 1 unread notifications

Marking all notifications as read empties the unread count
    # Given
    I am authenticated as admin
    I create a project named Notifications-MarkAll
    I create a user named inbox-eve with password eve123
    The inbox of inbox-eve is drained with password eve123
    I start an execution titled Run M assigned to inbox-eve
    I start an execution titled Run N assigned to inbox-eve
    I log in as inbox-eve with password eve123

    # When
    I mark all notifications as read

    # Then
    I have 0 unread notifications

Notifications are isolated per user
    # Given
    I am authenticated as admin
    I create a project named Notifications-Isolation
    I create a user named inbox-frank with password frank123
    I create a user named inbox-grace with password grace123
    The inbox of inbox-frank is drained with password frank123
    The inbox of inbox-grace is drained with password grace123
    I start an execution titled For Frank assigned to inbox-frank

    # When
    I log in as inbox-frank with password frank123

    # Then
    I have 1 unread notifications

    # And
    I log in as inbox-grace with password grace123
    I have 0 unread notifications

Assigning an execution to the creator does not produce a notification
    # Given
    I am authenticated as admin
    I create a project named Notifications-SelfAssign

    # When
    I start an execution titled My own run assigned to ${ADMIN_USER}

    # Then
    I have no unread notifications mentioning My own run
