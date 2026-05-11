*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I sign in to the UI as ${ADMIN_USER} with password ${ADMIN_PASS}
Suite Teardown    I tear down the frontend suite
Test Setup        I have a fresh project named ${PROJECT_NAME}


*** Variables ***
${ADMIN_USER}      %{TESTJAM_USER=admin}
${ADMIN_PASS}      %{TESTJAM_PASS=admin123}
${PROJECT_NAME}    UI-Members-Project


*** Test Cases ***
Adding a tester to the project lists them as a member
    # Given
    I create a user named ui-bob with password pw12345
    I open the members page

    # When
    I add ui-bob to the project as tester via the UI

    # Then
    The project members should include ui-bob
    The role of ui-bob should be tester

Changing a member role updates the persisted role
    # Given
    I create a user named ui-carol with password pw12345
    I open the members page
    I add ui-carol to the project as tester via the UI

    # When
    I change ui-carol role to viewer via the UI

    # Then
    The role of ui-carol should be viewer

Removing a member drops them from the list
    # Given
    I create a user named ui-dave with password pw12345
    I open the members page
    I add ui-dave to the project as viewer via the UI

    # When
    I remove ui-dave from the project via the UI

    # Then
    The project members should not include ui-dave
