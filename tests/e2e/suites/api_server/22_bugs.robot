*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    I clean up the current project


*** Test Cases ***
Create a bug and check it is numbered #1
    # Given
    I am authenticated as admin
    I create a project named Bug Project

    # When
    I create a bug titled Login crash

    # Then
    The project should have 1 bugs

Transition a bug through its status flow
    # Given
    I am authenticated as admin
    I create a project named Status Flow Project
    I create a bug titled Cant submit form

    # When
    I change the bug status to in_progress
    I change the bug status to resolved

    # Then
    The bug should have status resolved
    The bug history should contain 3 entries

Comment on a bug
    # Given
    I am authenticated as admin
    I create a project named Comment Project
    I create a bug titled Crash on logout

    # When
    I comment on the bug with Repro on staging

    # Then
    The bug should have 1 comments

Download the HTML report for a project
    # Given
    I am authenticated as admin
    I create a project named Report Project
    I create a critical bug titled Outage

    # When
    I download the bug report as html

    # Then
    The response status should be 200
    The downloaded bug report should be HTML
