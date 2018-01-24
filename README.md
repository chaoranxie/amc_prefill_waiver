# prefill_amc_waiver
Auto fill the amc release form with participants info
## Setup
```
pip install -r requirements.txt
```
## Download the participants csv file
```
click `Export to Tab Delimited` on the Roster page on regi
```
## Fill release form
```
python prefill_waiver.py static/waiver.pdf static/sample_participants.csv
```

## You should see following files in the static directory
```
waiver_filled_1.pdf (10 participants)
waiver_filled_2.pdf (1 participant)

```
## Sample
![Image of filed release form](sample.png)
