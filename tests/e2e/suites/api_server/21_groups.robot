*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    I delete the group


*** Test Cases ***
Admins can create and rename a group
    # Given
    I am authenticated as admin

    # When
    I create a group named QA-Team
    I rename the group to QA-Reviewers

    # Then
    The group name should be QA-Reviewers

Adding users to a group counts them as members
    # Given
    I am authenticated as admin
    I create a group named Group-Reviewers
    I create a user named gp-alice with password pw1234
    I create a user named gp-bob with password pw1234

    # When
    I add gp-alice to the current group
    I add gp-bob to the current group

    # Then
    The group should have 2 members
    The group should contain gp-alice
    The group should contain gp-bob

Removing a user from the group drops them
    # Given
    I am authenticated as admin
    I create a group named Group-Removal
    I create a user named gp-carol with password pw1234
    I add gp-carol to the current group

    # When
    I remove gp-carol from the current group

    # Then
    The group should have 0 members
