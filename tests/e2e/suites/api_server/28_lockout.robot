*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Setup       I am authenticated as admin
Test Teardown    I purge users with prefix lockout-


*** Variables ***
${LOCK_USER}      lockout-bob
${LOCK_EMAIL}     lockout-bob@test.com
${REAL_PASS}      real-secret-pw
${RESET_PASS}     fresh-pw-after-reset


*** Test Cases ***
Five wrong attempts lock the account
    # Given
    I create a user named ${LOCK_USER} with password ${REAL_PASS}

    # When
    I make 5 failed login attempts as ${LOCK_USER}

    # Then
    I try to log in as ${LOCK_USER} with password ${REAL_PASS}
    The response status should be 423

A locked account rejects even the correct password
    # Given
    I create a user named ${LOCK_USER} with password ${REAL_PASS}
    I make 5 failed login attempts as ${LOCK_USER}

    # When
    I try to log in as ${LOCK_USER} with password ${REAL_PASS}

    # Then
    The response status should be 423

Successful login below the threshold resets the counter
    # Given
    I create a user named ${LOCK_USER} with password ${REAL_PASS}
    I make 4 failed login attempts as ${LOCK_USER}

    # When
    I try to log in as ${LOCK_USER} with password ${REAL_PASS}
    The response status should be 200
    I make 4 failed login attempts as ${LOCK_USER}

    # Then
    I try to log in as ${LOCK_USER} with password ${REAL_PASS}
    The response status should be 200

Confirming a password reset clears an existing lock
    # Given
    I create a user named ${LOCK_USER} with password ${REAL_PASS}
    I make 5 failed login attempts as ${LOCK_USER}
    I purge emails to ${LOCK_EMAIL}
    I request a password reset for ${LOCK_EMAIL}
    I wait for 1 emails to ${LOCK_EMAIL}
    ${token}=    I extract the password reset token from the email to ${LOCK_EMAIL}

    # When
    I confirm the password reset with token ${token} and password ${RESET_PASS}

    # Then
    The response status should be 204
    I try to log in as ${LOCK_USER} with password ${RESET_PASS}
    The response status should be 200
