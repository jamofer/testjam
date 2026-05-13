*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Setup       Reset password feature is ready
Test Teardown    I purge users with prefix reset-


*** Variables ***
${TARGET_USER}     reset-alice
${TARGET_EMAIL}    reset-alice@test.com
${ORIGINAL_PASS}   original-pw
${NEW_PASS}        replaced-secret-1


*** Test Cases ***
Requesting a reset for an existing user emails them
    # Given
    I create a user named ${TARGET_USER} with password ${ORIGINAL_PASS}

    # When
    I request a password reset for ${TARGET_EMAIL}

    # Then
    The response status should be 204
    I wait for 1 emails in the mailbox
    The latest email recipient should be ${TARGET_EMAIL}
    The latest email subject should contain Reset your password

Requesting a reset for an unknown email returns 204 silently
    # When
    I request a password reset for ghost@nowhere.com

    # Then
    The response status should be 204
    The mailbox should be empty

Confirming with a valid token lets the user log in with the new password
    # Given
    I create a user named ${TARGET_USER} with password ${ORIGINAL_PASS}
    I request a password reset for ${TARGET_EMAIL}
    I wait for 1 emails in the mailbox
    ${token}=    I extract the password reset token from the latest email

    # When
    I confirm the password reset with token ${token} and password ${NEW_PASS}

    # Then
    The response status should be 204
    I try to log in as ${TARGET_USER} with password ${NEW_PASS}
    The response status should be 200
    I try to log in as ${TARGET_USER} with password ${ORIGINAL_PASS}
    The response status should be 401

Confirming twice with the same token fails the second time
    # Given
    I create a user named ${TARGET_USER} with password ${ORIGINAL_PASS}
    I request a password reset for ${TARGET_EMAIL}
    I wait for 1 emails in the mailbox
    ${token}=    I extract the password reset token from the latest email
    I confirm the password reset with token ${token} and password ${NEW_PASS}
    The response status should be 204

    # When
    I confirm the password reset with token ${token} and password another-password-123

    # Then
    The response status should be 400

Confirming with a bogus token returns 400
    # When
    I confirm the password reset with token totally-not-a-real-token and password ${NEW_PASS}

    # Then
    The response status should be 400


*** Keywords ***
Reset password feature is ready
    The email pipeline is reset
    I configure SMTP to use mailpit
