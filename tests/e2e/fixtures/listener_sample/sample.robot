*** Settings ***
Documentation    Tiny RF suite used by the listener integration smoke test.


*** Test Cases ***
Successful smoke check
    Log    booting the system
    Log    sanity passing
    Should Be Equal    1    1

Failing smoke check
    Log    attempting an impossible assertion
    Should Be Equal    1    2

Multi-step flow
    Open the login form
    Submit the login form


*** Keywords ***
Open the login form
    Log    navigating to /login
    Log    waiting for the form to render

Submit the login form
    Log    typing the username
    Log    clicking submit
