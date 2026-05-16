*** Settings ***
Documentation    Browser-driven tests against the Testjam React frontend.
...              Uses the Browser (Playwright) library against http://frontend:5173.
Library          testjam_e2e.testjam_library.TestjamLibrary
Suite Setup      the admin locale is en
