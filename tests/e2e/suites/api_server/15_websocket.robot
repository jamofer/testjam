*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    The websocket session is cleaned up


*** Test Cases ***
Subscribing to my own user topic succeeds
    # Given
    I am authenticated as admin
    I open a websocket

    # When
    I subscribe to my user topic

    # Then
    The last websocket frame event should be subscribed

Subscribing to a project topic succeeds for an authenticated user
    # Given
    I am authenticated as admin
    I create a project named WS-Project
    I open a websocket

    # When
    I subscribe to the current project topic

    # Then
    The last websocket frame event should be subscribed

Subscribing to another users user topic is forbidden
    # Given
    I am authenticated as admin
    I create a user named mallory with password mall123
    I open a websocket

    # When
    I try to subscribe to the user topic of mallory

    # Then
    The last websocket frame should be an error with reason forbidden

Subscribing to a malformed topic is rejected
    # Given
    I am authenticated as admin
    I open a websocket

    # When
    I try to subscribe to topic project:not-a-number

    # Then
    The last websocket frame should be an error with reason invalid_topic

Pong action is silently accepted
    # Given
    I am authenticated as admin
    I open a websocket
    I send a pong frame

    # When
    I subscribe to my user topic

    # Then
    The last websocket frame event should be subscribed

Step result log broadcasts arrive on the execution topic
    # Given
    I am authenticated as admin
    I have a live-ready execution with one step Run
    I start a step result for step Run
    I open a websocket
    I subscribe to the current execution topic

    # When
    I append a INFO log line streaming live

    # Then
    I should receive a step_result.log_appended event within 3 seconds
    The last websocket payload entries should contain message streaming live
