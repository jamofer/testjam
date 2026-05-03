*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Test Cases ***
Successful admin login
    # Given the admin credentials exist
    I am authenticated as admin
    # When I check the current user
    # Then the identity is correct
    The current user should be admin

Login with wrong password returns 401
    # Given invalid credentials
    I try to log in as admin with password wrongpassword
    # Then the response is rejected
    The response status should be 401

Login with unknown user returns 401
    # Given a user that does not exist
    I try to log in as ghost with password ghost123
    # Then the response is rejected
    The response status should be 401

Valid credentials give access to protected resource
    # Given a logged-in session
    I am authenticated as admin
    # When I request a protected endpoint
    # Then it succeeds
    The current user should be admin
