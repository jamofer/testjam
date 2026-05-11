*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Setup    Admin notification preferences are reset to defaults


*** Test Cases ***
Default preferences cover the three execution events
    # Given
    I am authenticated as admin

    # Then
    The execution_assigned preference should be in-app true email true
    The execution_finished preference should be in-app true email false
    The execution_failed preference should be in-app true email true

Disabling email persists across requests
    # Given
    I am authenticated as admin

    # When
    I disable email notifications for execution_failed

    # Then
    The execution_failed preference should be in-app true email false

Re-enabling email restores the channel
    # Given
    I am authenticated as admin
    I disable email notifications for execution_failed

    # When
    I enable email notifications for execution_failed

    # Then
    The execution_failed preference should be in-app true email true

Disabling in-app skips the channel entirely
    # Given
    I am authenticated as admin

    # When
    I disable in-app notifications for execution_assigned

    # Then
    The execution_assigned preference should be in-app false email false

Setting both channels in one call works
    # Given
    I am authenticated as admin

    # When
    I set execution_assigned preferences to in-app false email true

    # Then
    The execution_assigned preference should be in-app false email true

Preferences are isolated per user
    # Given
    I am authenticated as admin
    I create a user named grace with password grace123
    I disable email notifications for execution_failed

    # When
    I log in as grace with password grace123

    # Then
    The execution_failed preference should be in-app true email true

Requesting an unknown event returns 400
    # Given
    I am authenticated as admin

    # Then
    Requesting preferences for totally_made_up should fail with 400
