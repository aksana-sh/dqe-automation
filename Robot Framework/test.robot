*** Settings ***
Library    SeleniumLibrary
Library    Collections
Library    helper.py

*** Variables ***
${REPORT_FILE}        C:/Users/Aksana_Shchukina/Desktop/DQ_Automation/report.html
${PARQUET_FOLDER}     C:/Users/Aksana_Shchukina/Desktop/DQ_Automation/parquet_data/facility_type_avg_time_spent_per_visit_date
${START_DATE}         2026-03-13
${END_DATE}           2026-03-19


*** Keywords ***
Read HTML Table To DataFrame
    ${table}=    Get WebElement    //*[contains(@class, "table")]
    ${html_df}=  Read Html Table   ${table}
    RETURN       ${html_df}

Read Parquet Data To DataFrame
    ${parquet_df}=  Read Parquet Data    ${PARQUET_FOLDER}    ${START_DATE}    ${END_DATE}
    RETURN          ${parquet_df}

Compare DataFrames Should Match
    [Arguments]    ${html_df}    ${parquet_df}

    ${result}=        Compare Dataframes     ${html_df}   ${parquet_df}
    ${msg}=           Get From Dictionary    ${result}    message
    ${html_only}=     Get From Dictionary    ${result}    html_only
    ${parquet_only}=  Get From Dictionary    ${result}    parquet_only

    ${rows1}=    Get Length    ${html_only}
    ${rows2}=    Get Length    ${parquet_only}

    Run Keyword If    ${rows1} > 0 or ${rows2} > 0    Fail    ${msg}


*** Test Cases ***
Validate HTML Report Against Parquet Dataset
    Open Browser    file://${REPORT_FILE}    chrome
    Maximize Browser Window
    Wait Until Page Contains Element    //*[contains(@class, "table")]    5s

    ${html_df}=       Read HTML Table To DataFrame
    ${parquet_df}=    Read Parquet Data To DataFrame
    Compare DataFrames Should Match    ${html_df}    ${parquet_df}

    Close Browser
