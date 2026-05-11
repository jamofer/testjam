*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary


*** Test Cases ***
Admin can deactivate and reactivate a user
    # Given
    I am authenticated as admin
    I create a user named alice-toggle with password pw12345

    # When
    I deactivate user alice-toggle

    # Then
    The user alice-toggle should be inactive

    # When
    I activate user alice-toggle

    # Then
    The user alice-toggle should be active

A deactivated user cannot log in
    # Given
    I am authenticated as admin
    I create a user named alice-locked with password pw12345
    I deactivate user alice-locked

    # When
    I try to log in as alice-locked with password pw12345

    # Then
    The response status should be 403

Admin can delete a user
    # Given
    I am authenticated as admin
    I create a user named alice-doomed with password pw12345

    # When
    I delete user alice-doomed

    # Then
    The user alice-doomed should no longer exist

Updating my profile email persists
    # Given
    I am authenticated as admin
    I create a user named profile-bob with password pw12345
    I log in as profile-bob with password pw12345

    # When
    I update my email to bob-new@test.com

    # Then
    The current user email should be bob-new@test.com

Updating my full name persists
    # Given
    I am authenticated as admin
    I create a user named profile-carol with password pw12345
    I log in as profile-carol with password pw12345

    # When
    I update my full name to Carol Surname

    # Then
    The current user full name should be Carol Surname

Changing my password lets me log in with the new credentials
    # Given
    I am authenticated as admin
    I ensure user passwd-dave has password pw12345
    I log in as passwd-dave with password pw12345

    # When
    I change my password from pw12345 to brandnew99

    # Then
    I log in as passwd-dave with password brandnew99

Changing my password fails when the current password is wrong
    # Given
    I am authenticated as admin
    I ensure user passwd-eve has password pw12345
    I log in as passwd-eve with password pw12345

    # When
    I try to change my password from wrong-current to anything-new

    # Then
    The response status should be 400

Non-admin users cannot delete other users
    # Given
    I am authenticated as admin
    I create a user named victim-frank with password pw12345
    I create a user named attacker-grace with password pw12345
    I log in as attacker-grace with password pw12345

    # When
    I try to delete user victim-frank

    # Then
    The response status should be 403

    # And
    I am authenticated as admin
    The user victim-frank should be active

Non-admin users cannot deactivate other users
    # Given
    I am authenticated as admin
    I create a user named victim-henry with password pw12345
    I create a user named attacker-irene with password pw12345
    I log in as attacker-irene with password pw12345

    # When
    I try to deactivate user victim-henry

    # Then
    The response status should be 403

Non-admin users cannot create new users
    # Given
    I am authenticated as admin
    I create a user named attacker-jack with password pw12345
    I log in as attacker-jack with password pw12345

    # When
    I try to create a user named smuggled-kate with password pw12345

    # Then
    The response status should be 403
