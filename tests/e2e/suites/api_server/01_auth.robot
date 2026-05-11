*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Variables ***
${ADMIN_USER}    %{TESTJAM_USER=admin}


*** Test Cases ***
Successful admin login
    # Given
    I am authenticated as admin

    # Then
    The current user should have admin privileges

Login with wrong password returns 401
    # When
    I try to log in as ${ADMIN_USER} with password wrongpassword

    # Then
    The response status should be 401

Login with unknown user returns 401
    # When
    I try to log in as ghost with password ghost123

    # Then
    The response status should be 401

Valid credentials give access to protected resource
    # Given
    I am authenticated as admin

    # Then
    The current user should have admin privileges
