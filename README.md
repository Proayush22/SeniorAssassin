# Senior Assassin Team Generator
Senior Assassin Team Generator
This project automates team communication and payment verification for Senior Assassin duos and trios.

It consists of two main Python scripts:

csvemail.py
This script takes CSV exports of contacts and payments from HubSpot. It checks that all participants have completed payment and generates a new CSV file, team_data.csv, containing verified teams.

finalemail.py
This script reads team_data.csv and sends customized confirmation emails to each participant using SMTP through a Google account.

How It Works:
Export your contacts and payments CSV files from HubSpot.

Run csvemail.py to verify payments and create team_data.csv.

Run finalemail.py to automatically email all verified participants.

Would you also like me to help you add a small "Usage" section, some badges (like Python version, dependencies), or a quick setup guide? That would make it even more GitHub-ready! 🚀







You said:
yeah sure
ChatGPT said:
Great! Here's an expanded version of the README that includes:

Setup instructions

Usage examples

Requirements section (Python packages)

A clean layout that's professional for GitHub

Senior Assassin Team Generator
Automate team verification and email notifications for Senior Assassin duos and trios.

This project ensures all participants are verified (based on payment status) and sends out custom confirmation emails automatically.

Features
Verifies participant payments from HubSpot CSV exports.

Generates a team_data.csv of verified teams.

Sends emails to participants using SMTP and a Google account.

Requirements
Python 3.8+

pandas

smtplib (comes with Python)

email (comes with Python)

Google Account with SMTP access enabled (e.g., App Passwords if using Gmail)

Install pandas with:

bash
Copy
Edit
pip install pandas
Setup
Export your Contacts and Payments CSV files from HubSpot.

Save them in the project directory.

Update your Google account credentials inside finalemail.py:

python
Copy
Edit
EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"
Make sure you have Allow less secure apps enabled or use an App Password if your Google Account has 2FA (Two-Factor Authentication).

Usage
Step 1: Verify and Prepare Team Data
Run the following:

bash
Copy
Edit
python csvemail.py
This reads your Contacts and Payments CSVs.

Verifies that everyone has paid.

Creates a new file called team_data.csv with valid participants.

Step 2: Send Emails
Then, run:

bash
Copy
Edit
python finalemail.py
This sends personalized emails to all verified players listed in team_data.csv.

File Structure
bash
Copy
Edit
csvemail.py       # Processes and verifies HubSpot CSVs
finalemail.py     # Sends emails using the verified team data
team_data.csv     # Output file with verified participants (generated)
contacts.csv      # Input file from HubSpot (you provide)
payments.csv      # Input file from HubSpot (you provide)
Notes
This is specifically built for duos and trios for Senior Assassin.

Make sure your Google account SMTP settings are configured correctly.

Double-check your spam/junk folders during testing.