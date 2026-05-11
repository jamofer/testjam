*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    Settings are reset to defaults


*** Test Cases ***
Public settings are anonymously readable
    # Given
    I sign out

    # Then
    The public settings app name should be Testjam
    The public settings should allow registration

Admins read full settings with the SMTP password masked
    # Given
    I am authenticated as admin

    # Then
    The SMTP password should be not set

Configuring SMTP flips the public smtp_configured flag
    # Given
    I am authenticated as admin
    The public settings should report SMTP as not configured

    # When
    I configure SMTP host smtp.example.com port 587 from noreply@example.com

    # Then
    The public settings should report SMTP as configured
    The admin settings SMTP host should be smtp.example.com

SMTP password can be set and cleared
    # Given
    I am authenticated as admin
    I configure SMTP host smtp.example.com port 587 from noreply@example.com

    # When
    I set the SMTP password to s3cret

    # Then
    The SMTP password should be set

    # When
    I clear the SMTP password

    # Then
    The SMTP password should be not set

Reply-to address persists
    # Given
    I am authenticated as admin

    # When
    I set the reply-to address to support@example.com

    # Then
    The admin settings reply-to should be support@example.com

Log flush interval persists
    # Given
    I am authenticated as admin

    # When
    I set the log flush interval to 250 milliseconds

    # Then
    The admin settings log flush interval should be 250 milliseconds

Disabling self-registration hides it in the public payload
    # Given
    I am authenticated as admin
    The public settings should allow registration

    # When
    I disable self-registration

    # Then
    The public settings should not allow registration

Non-admin users cannot read admin settings
    # Given
    I am authenticated as admin
    I create a user named viewer1 with password vw123
    I log in as viewer1 with password vw123

    # When
    I try to fetch the admin settings

    # Then
    The response status should be 403

Anonymous requests to admin settings are rejected
    # Given
    I sign out

    # When
    I try to fetch the admin settings

    # Then
    The response status should be 401
