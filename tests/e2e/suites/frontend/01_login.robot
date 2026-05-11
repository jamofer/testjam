*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       I open a headless browser
Suite Teardown    I tear down the frontend suite


*** Variables ***
${ADMIN_USER}    %{TESTJAM_USER=admin}
${ADMIN_PASS}    %{TESTJAM_PASS=admin123}


*** Test Cases ***
The login page renders the Testjam branding
    # Given
    I open the login page

    # Then
    The page title should contain Testjam

Valid credentials land on the projects page
    # Given
    I open the login page

    # When
    I submit the login form with ${ADMIN_USER} and ${ADMIN_PASS}

    # Then
    I should land on the projects page

Wrong password surfaces an error in the login form
    # Given
    I open the login page

    # When
    I submit the login form with ${ADMIN_USER} and definitely-wrong

    # Then
    The login form should show error Invalid credentials
