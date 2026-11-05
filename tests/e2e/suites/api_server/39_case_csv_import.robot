*** Settings ***
Library    testjam_e2e.testjam_library.TestjamLibrary
Test Teardown    I clean up the current project


*** Variables ***
${CASES_CSV}        ${CURDIR}/../../fixtures/cases.csv
${EXCEL_CSV}        ${CURDIR}/../../fixtures/cases_excel.csv


*** Test Cases ***
Importing a CSV creates the cases inside their nested suites
    # Given
    I am authenticated as admin
    I create a project named Case-Csv-Import

    # When
    I import test cases from ${CASES_CSV}

    # Then
    The case import should have created 3 cases and 3 suites
    The case import should report errors on rows 5
    The suite Payments should contain cases Pay with card, Pay with voucher
    The suite Login should contain cases Log in with valid credentials

Imported cases keep their tags and steps
    # Given
    I am authenticated as admin
    I create a project named Case-Csv-Details

    # When
    I import test cases from ${CASES_CSV}

    # Then
    The case Pay with card of suite Payments should have tags payments, smoke
    The case Pay with card of suite Payments should have steps Open the cart, Pay with card

Importing the same CSV twice reports the duplicates
    # Given
    I am authenticated as admin
    I create a project named Case-Csv-Duplicates
    I import test cases from ${CASES_CSV}

    # When
    I import test cases from ${CASES_CSV}

    # Then
    The case import should have created 0 cases and 0 suites
    The case import should report errors on rows 2, 3, 4, 5

An Excel export with semicolons and Windows encoding imports as it is
    # Given
    I am authenticated as admin
    I create a project named Case-Csv-Excel

    # When
    I import test cases from ${EXCEL_CSV}

    # Then
    The case import should have created 1 cases and 1 suites
    The case import should report no errors
    The suite Configuración should contain cases Cambiar contraseña
