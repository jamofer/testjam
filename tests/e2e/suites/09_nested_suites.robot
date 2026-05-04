*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Test Cases ***
Create a sub-suite inside a parent suite
    [Teardown]    I clean up the current project
    I am authenticated as admin
    I create a project named Nested Suite Project
    I create a suite named Parent Suite
    I create a sub-suite named Child Suite inside the current suite
    The current suite should have 1 child suites
    The child suites list should contain the sub-suite

Root suite list does not include child suites
    [Teardown]    I clean up the current project
    I am authenticated as admin
    I create a project named Root List Project
    I create a suite named Top Level Suite
    I create a sub-suite named Nested Suite inside the current suite
    The project should have 1 suites

Multiple child suites under one parent
    [Teardown]    I clean up the current project
    I am authenticated as admin
    I create a project named Multi Child Project
    I create a suite named Parent
    I create a sub-suite named Child A inside the current suite
    I create a sub-suite named Child B inside the current suite
    The current suite should have 2 child suites
