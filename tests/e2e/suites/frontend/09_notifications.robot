*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I sign in to the UI as ${ADMIN_USER} with password ${ADMIN_PASS}
Suite Teardown    I tear down the frontend suite
Test Setup        I log in as ${ADMIN_USER} with password ${ADMIN_PASS}
Test Teardown     I log in as ${ADMIN_USER} with password ${ADMIN_PASS}


*** Variables ***
${ADMIN_USER}      %{TESTJAM_USER=admin}
${ADMIN_PASS}      %{TESTJAM_PASS=admin123}


*** Test Cases ***
Assignment notifications surface as an unread bell badge
    # Given
    I have a recipient notif-alice with password pw12345 expecting an assignment

    # Then
    The notification badge should show 1 unread

Opening the drawer shows the assignment entry
    # Given
    I have a recipient notif-bob with password pw12345 expecting an assignment

    # When
    I open the notifications drawer

    # Then
    The notifications drawer should list 1 unread entries

Marking all read clears the bell badge
    # Given
    I have a recipient notif-carol with password pw12345 expecting an assignment
    I open the notifications drawer

    # When
    I mark all notifications as read via the UI

    # Then
    The notification badge should be hidden

A clean recipient sees an empty drawer
    # Given
    I have a recipient notif-dan with password pw12345 and no notifications

    # When
    I open the notifications drawer

    # Then
    The notifications drawer should be empty
