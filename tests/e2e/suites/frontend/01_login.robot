*** Settings ***
Library    Browser
Library    testjam_e2e.testjam_library.TestjamLibrary
Suite Setup       Open headless browser
Suite Teardown    Close Browser    ALL


*** Variables ***
${FRONTEND_URL}    %{TESTJAM_FRONTEND_URL=http://frontend:5173}


*** Keywords ***
Open headless browser
    New Browser    chromium    headless=true
    New Context    viewport={'width': 1280, 'height': 800}    ignoreHTTPSErrors=True

Open login page
    New Page    ${FRONTEND_URL}/login
    Wait For Elements State    input[name="username"]    visible    timeout=10s


*** Test Cases ***
Login page renders
    Open login page
    Get Title    contains    Testjam

Successful login lands on projects
    Open login page
    Fill Text    input[name="username"]    %{TESTJAM_ADMIN_USER=admin}
    Fill Text    input[name="password"]    %{TESTJAM_ADMIN_PASS=admin123}
    Click    button[type="submit"]
    Wait Until Network Is Idle    timeout=10s
    Get Url    contains    /projects

Login with wrong password shows error
    Open login page
    Fill Text    input[name="username"]    %{TESTJAM_ADMIN_USER=admin}
    Fill Text    input[name="password"]    definitely-wrong
    Click    button[type="submit"]
    Wait For Elements State    p.text-red-500    visible    timeout=10s
    Get Text    p.text-red-500    contains    Invalid credentials
