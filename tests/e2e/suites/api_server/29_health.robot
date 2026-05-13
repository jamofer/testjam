*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Test Cases ***
Health endpoint reports the database as up
    # When
    I check the health endpoint

    # Then
    The response status should be 200
    The health payload should report status ok
    The health payload should report db ok
    The health payload should report a non-empty version

Health endpoint does not require authentication
    # When
    I check the health endpoint

    # Then
    The response status should be 200
