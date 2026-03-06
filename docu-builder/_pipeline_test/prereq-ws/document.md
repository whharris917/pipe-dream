==============================================================================
  CR-TEST: Prerequisite Test
  Phase: EXECUTION
==============================================================================

  --------------------------------------------------------------------------
  Section steps: Test Steps
  Status: EXECUTION
  --------------------------------------------------------------------------

  [Table 0: Test Steps] [EXTENDABLE]
  | Step (ID) | Task (Design)         | Prereq (Prereq) | Result (Recorded Value)         | Sign (Signature) |
  |-----------|-----------------------|-----------------|---------------------------------|------------------|
  | S-1       | Setup environment     |                 | Environment ready               | alice            |
  | S-2       | Run unit tests        | S-1 complete    | All 42 unit tests pass          | bob              |
  | S-3       | Run integration tests | S-2 complete    | Integration tests pass          | bob              |
  | S-4       | Deploy to staging     | S-3 complete    | Deployed to staging.example.com | carol            |
  | [+ Add Row]                                                                                               |
  Progress: 8/8 cells executed

------------------------------------------------------------------------------
  EXECUTION COMMANDS:
    nav <section_id>              -- Navigate to section
    view_all                      -- Show all sections at once
    exec <section_id> <table_index> <row_index> <column>=<value>
    amend <section_id> <table_index> <row_index> <column>=<value> reason=<text>
    add_row <section_id> <table_index> col=val ...
                                    (extendable tables only)
------------------------------------------------------------------------------
  Write your command below, then save this file.

>> 