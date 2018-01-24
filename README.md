# amc_autofill_release_form
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
python fill_release_form.py release_form.pdf sample_participants.csv
```

## You should see following files in the directory
```
release_form_filled_1.pdf
release_form_filled_2.pdf (10 participants per file)

```
## Sample
![Image of filed release form](sample.png)
