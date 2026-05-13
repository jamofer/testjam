*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Setup       Self-delete user is fresh
Test Teardown    Self-delete teardown


*** Variables ***
${ADMIN_USER}    %{TESTJAM_USER=admin}
${ADMIN_PASS}    %{TESTJAM_PASS=admin123}
${SELF_USER}     sd-self
${SELF_PASS}     pw-self


*** Test Cases ***
Self-delete is rejected when admin disables it
    # Given
    I disable user self deletion
    I log in as ${SELF_USER} with password ${SELF_PASS}

    # When
    I delete my account

    # Then
    The response status should be 403

Self-delete works when admin enables it
    # Given
    I enable user self deletion
    I log in as ${SELF_USER} with password ${SELF_PASS}

    # When
    I delete my account

    # Then
    The response status should be 204
    I log in as ${ADMIN_USER} with password ${ADMIN_PASS}
    user ${SELF_USER} should be marked as deleted


*** Keywords ***
Self-delete user is fresh
    I am authenticated as admin
    I create a user named ${SELF_USER} with password ${SELF_PASS}

Self-delete teardown
    I log in as ${ADMIN_USER} with password ${ADMIN_PASS}
    I disable user self deletion
    I purge users with prefix sd-
