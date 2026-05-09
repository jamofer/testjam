*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Test Cases ***
Create a plan inside a project
    [Teardown]    I clean up the current project
    # Given a project
    I am authenticated as admin
    I create a project named Plan Project
    # When I create a plan
    I create a plan titled Smoke Suite
    # Then the plan is stored
    The plan title should be Smoke Suite
    The project should have 1 plans

Rename a plan
    [Teardown]    I clean up the current project
    # Given a plan
    I am authenticated as admin
    I create a project named Rename Plan Project
    I create a plan titled Original Plan
    # When I rename it
    I rename the plan to Renamed Plan
    # Then the updated title is returned
    The plan title should be Renamed Plan

Add a case to a plan
    [Teardown]    I clean up the current project
    # Given a plan and a case
    I am authenticated as admin
    I create a project named Plan Cases Project
    I create a suite named Login
    I create a test case named TC Login
    I create a plan titled Sprint 1
    # When I add the case to the plan
    I add the current case to the plan
    # Then the plan contains the case
    The plan should contain the current case
    The plan should have 1 cases

Disassociate a case from a plan via PUT
    [Teardown]    I clean up the current project
    # Given a plan with one case
    I am authenticated as admin
    I create a project named Disassociate Project
    I create a suite named Suite A
    I create a test case named TC Disposable
    I create a plan titled Throwaway Plan
    I add the current case to the plan
    # When I replace plan cases with empty list
    I replace plan cases with ${EMPTY}
    # Then the case is no longer in the plan
    The plan should not contain the current case
    The plan should have 0 cases

Add multiple cases to a plan
    [Teardown]    I clean up the current project
    # Given a plan and three cases
    I am authenticated as admin
    I create a project named Multi Cases Plan
    I create a suite named Suite Multi
    ${id1}=    I create a test case named TC One
    ${id2}=    I create a test case named TC Two
    ${id3}=    I create a test case named TC Three
    I create a plan titled Big Plan
    # When I add all three to the plan
    I add cases ${id1},${id2},${id3} to the plan
    # Then the plan reports three cases
    The plan should have 3 cases

Delete a plan
    [Teardown]    I clean up the current project
    # Given a plan
    I am authenticated as admin
    I create a project named Delete Plan Project
    I create a plan titled Goodbye Plan
    # When I delete it
    I delete the plan
    # Then the plan is gone
    The plan should no longer exist

Adding a case twice does not duplicate
    [Teardown]    I clean up the current project
    # Given a plan with a case already attached
    I am authenticated as admin
    I create a project named Dedup Plan Project
    I create a suite named Suite Dedup
    I create a test case named TC Dedup
    I create a plan titled Dedup Plan
    I add the current case to the plan
    # When I add the same case again
    I add the current case to the plan
    # Then the plan still has only one case
    The plan should have 1 cases

Project accumulates multiple plans
    [Teardown]    I clean up the current project
    # Given a project
    I am authenticated as admin
    I create a project named Multi Plan Project
    # When I create three plans
    I create a plan titled Plan A
    I create a plan titled Plan B
    I create a plan titled Plan C
    # Then all three are listed
    The project should have 3 plans
