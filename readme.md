congress-turk
=============

A library for gathering Congress district office data through Mechanical Turk.

Background
----------

There is no central data source for information on US legislators' district
offices. However, this information is useful to citizens and advocacy
organizations wishing to contact legislators via their local offices.

<https://github.com/TheWalkers/congress-legislators> contains a file 
(legislators-district-offices.yaml) with machine and human readable list of
district offices, released into the public domain from a manually compiled 
source.

However, maintaining this data source is a challenge. There are 
535 Representatives and Senators (in addition to non-voting delegates),
each of which has at least one and perhaps as many as ten district offices.
In 2016, this amounted to nearly 1500 offices, each with address, phone and 
fax numbers, contact hours, and other information.

These data are generally found on legislators' websites, but the websites 
themselves are not in any standard format, making machine-based data scraping
difficult.

This project contains scripts and pages to facilitate use of Amazon 
Mechanical Turk to have human workers identify and gather district office data.

Overview
--------

At present the process is largely manual, and relies on an operator to 
drive various pieces forward and reconcile results of Turk tasks.

There are two types of Human Intelligence Tasks (HITs) for which we rely on 
Mechanical Turk:

- List Offices: enter a list of district office names for a legislator
- Office Details: for a given district office, enter the contact details

The general process is:

- set up list and detail tasks on <http://requester.turk.com/>
- generate and upload list tasks
- reconcile the results of list tasks
- split list tasks into detail tasks and upload 
- reconcile results of detail tasks
- patch or replace legislator-district-offices.yaml with results

Scripts provided in this repository assist with these steps.

Set up HITs
-----------

1. Go to <https://requester.mturk.com/create/projects/new>

2. Create a List Offices task:
    - Mean / median times for this task were 221s / 53s, set reward accordingly
    - 2 assignments per HIT (for error correction)
    - Recommend NOT requiring "Masters" qualification
    - list_offices.html (and example screenshot office_list.png) 
        provides a sample layout.
    - test that example screenshot and URL links work in preview

3. Create an Office Details task
    - Mean / median times for this task were 475s / 133s, set reward accordingly
    - 2 assignments per HIT (for error correction)
    - Recommend NOT requiring "Masters" qualification
    - office_details.html (and example screenshot office_details.png) 
        provides a sample layout.
    - test that example screenshot and URL links work in preview

Create List Tasks
-----------------

1. Obtain a current list of legislators from congress-legislators repository
    <https://github.com/unitedstates/congress-legislators/>

2. Run:

    `python generate_hits.py congress-legislators/legislators-current.yaml
    [-a | desired targeting options] -o list_hits.csv`

3. Publish list_hits.csv as a List Offices task on 
    <https://requester.mturk.com/create/projects>

4. Wait for workers to complete the task.

List Task Results
-----------------

1. Download the CSV file of results from <https://requester.mturk.com/manage>
    when complete.

2. Reconcile the results by running:

    `python reconcile_list_results.py list_results.csv list_results_out.csv 
        list_results_review.csv`

3. This will enter an interactive program that will let you reconcile
    differences between answers supplied by Turk workers. (See help provided
    in the program for more information on this process.) The program tracks
    progress in the review file, so it can be interrupted (via ctrl-c) 
    and resumed later.

4. The program will produce two additional files:
    - an output file, with the reconciled results, one row per original HIT
    - a review file containing the Approve/Reject judgements which can be
        re-uploaded to mturk.com to provide feedback on incorrectly
        completed assignemnts.


Create Detail Tasks
-------------------

1. Split the reconciled list results into individual office detail tasks by 
    running:

    `python split_to_office_hits.py list_results_out.csv detail_hits.csv`

2. Publish detail_hits.csv on <https://requester.mturk.com/create/projects>

3. Wait for workers to complete the task.

Detail Task Results
-------------------

1. Download the CSV file of results from <https://requester.mturk.com/manage>
    when complete.

2. Reconcile the results by running:

    `python reconcile_detail_results.py detail_results.csv detail_results_out.csv 
    detail_results_review.csv`

3. As with List results reconciliation, this is an interactive, resumable
    program that lets the operator view discrepancies between worker 
    submissions and decide which version is correct.  (This is time-consuming!)

4. Same as List results, the program will produce two additional files:
    - an output file, with the reconciled results, one row per original HIT
    - a review file containing the Approve/Reject judgements which can be
        re-uploaded to mturk.com to provide feedback on incorrectly
        completed assignemnts.


Convert Detail Results
----------------------

1. Convert the csv file to yaml with:

    `python convert_office_results.py detail_results_out.csv 
    detail_results.yaml`

2. If this file represents all district offices, it can replace the existing
    file, with:

    `mv detail_results.yaml 
    congress-legislators/legislator-district-offices.yaml`

3. If this is an update to a subset of legislators' offices, patch in these 
    results with:

    `python patch_details.py detail_results.yaml 
    congress-legislators/legislator-district-offices.yaml`


Normalization and Geocoding
---------------------------

As a preprocessing step for detail reconciliation, this program can use
smarty streets to normalize address fields and geocode to a latitude and
longitude. This requires an API account, and credentials should be stored in
a `smarty_creds.py` file like this:

```
SMARTY_AUTH_ID = xxx
SMARTY_AUTH_TOKEN = xxx
```


Notes
-----

- Legislator websites can be ambiguous, so it makes sense to Approve all
    submissions as long a good-faith effort was made to give a valid answer.


Areas for improvement
---------------------

- add in other id types besides bioguide
- normalize / skip hours
- automate more of this via Mech Turk API
- hand more of this (e.g. reconciliation) off to workers 



