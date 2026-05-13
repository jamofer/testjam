*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Setup       I am authenticated as admin
Test Teardown    Soft-delete teardown


*** Variables ***
${TARGET_USER}      sd-target
${TARGET_PASS}      pw-target


*** Test Cases ***
Soft-deleted user disappears from default listing
    # Given
    I create a user named ${TARGET_USER} with password ${TARGET_PASS}

    # When
    I delete user ${TARGET_USER}

    # Then
    The user ${TARGET_USER} should no longer exist
    user ${TARGET_USER} should be marked as deleted

Soft-deleted user cannot log in
    # Given
    I create a user named ${TARGET_USER} with password ${TARGET_PASS}
    I delete user ${TARGET_USER}

    # When
    I try to log in as ${TARGET_USER} with password ${TARGET_PASS}

    # Then
    The response status should be 401

Restore brings the user back to active state
    # Given
    I create a user named ${TARGET_USER} with password ${TARGET_PASS}
    I delete user ${TARGET_USER}

    # When
    I restore user ${TARGET_USER}

    # Then
    The response status should be 200
    user ${TARGET_USER} should not be marked as deleted
    I try to log in as ${TARGET_USER} with password ${TARGET_PASS}
    The response status should be 200


*** Keywords ***
Soft-delete teardown
    I am authenticated as admin
    I purge users with prefix sd-
