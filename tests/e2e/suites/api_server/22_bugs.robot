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

Attach a file to a bug and list it back
    # Given
    I am authenticated as admin
    I create a project named Attach Bug Project
    I create a bug titled Repro pending

    # When
    I attach file fixtures/junit_results.xml to the bug

    # Then
    The bug should have 1 attachments
    The bug attachments should contain junit_results.xml

Delete a bug attachment removes it from the listing
    # Given
    I am authenticated as admin
    I create a project named Detach Bug Project
    I create a bug titled Cleanup
    I attach file fixtures/junit_results.xml to the bug
    I attach file fixtures/rf_output.xml to the bug

    # When
    I delete the bug attachment named junit_results.xml

    # Then
    The bug should have 1 attachments
    The bug attachments should contain rf_output.xml

Project members can download bug attachments
    # Given
    I am authenticated as admin
    I create a project named Download Bug Project
    I create a bug titled Attach me
    I attach file fixtures/junit_results.xml to the bug

    # When
    I try to download the bug attachment named junit_results.xml

    # Then
    The response status should be 200
