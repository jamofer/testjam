*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Setup       Project solely owned by departing user
Test Teardown    Owner reassign teardown


*** Variables ***
${ADMIN_USER}        %{TESTJAM_USER=admin}
${ADMIN_PASS}        %{TESTJAM_PASS=admin123}
${OWNER_USER}        or-owner
${OWNER_PASS}        pw-owner
${SUCCESSOR_USER}    or-successor
${SUCCESSOR_PASS}    pw-successor
${PROJECT_NAME}      Reassign-Subject


*** Test Cases ***
Deleting a sole owner without resolution returns 409
    # When
    I try to delete user ${OWNER_USER}

    # Then
    The response status should be 409

Reassigning ownership lets the deletion succeed
    # Given
    I create a user named ${SUCCESSOR_USER} with password ${SUCCESSOR_PASS}

    # When
    I delete user ${OWNER_USER} reassigning ${PROJECT_NAME} to ${SUCCESSOR_USER}

    # Then
    The response status should be 204
    user ${OWNER_USER} should be marked as deleted

Archiving the project lets the deletion succeed
    # When
    I delete user ${OWNER_USER} archiving ${PROJECT_NAME}

    # Then
    The response status should be 204
    user ${OWNER_USER} should be marked as deleted
    The project should be archived


*** Keywords ***
Project solely owned by departing user
    I am authenticated as admin
    I create a user named ${OWNER_USER} with password ${OWNER_PASS}
    I log in as ${OWNER_USER} with password ${OWNER_PASS}
    I create a project named ${PROJECT_NAME}
    I log in as ${ADMIN_USER} with password ${ADMIN_PASS}

Owner reassign teardown
    I am authenticated as admin
    I purge projects with prefix Reassign-
    I purge users with prefix or-
