import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time

# SMTP server settings
SMTP_SERVER = "smtp.gmail.com"  # Change to your email provider's SMTP server
SMTP_PORT = 587  # Change if your provider uses a different port
SENDER_EMAIL = "sbseniorassassin2025@gmail.com"  # Change to your email address
SENDER_PASSWORD = "mkcu dxtt mwdd amcj"  # Use an app password or your actual password

def send_email(to_emails, subject, body):
    """
    Send an email to one or more recipients
    """
    # Create message container
    message = MIMEMultipart()
    message['From'] = SENDER_EMAIL
    message['Subject'] = subject
    
    # Process email recipients
    if isinstance(to_emails, list):
        message['To'] = ", ".join(to_emails)
        recipients = to_emails
    else:
        message['To'] = to_emails
        recipients = [to_emails]
    
    # Add body to email
    message.attach(MIMEText(body, 'plain'))
    
    try:
        # Create SMTP session
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()  # Enable security
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            
            # Send email
            server.send_message(message)
            print(f"Successfully sent email to {', '.join(recipients)}")
            return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def read_csv_and_send_emails(csv_file):
    """
    Read the CSV file and send emails to each team about their target
    """
    teams_data = {}
    
    # First pass: Read all team data from CSV
    with open(csv_file, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            team_name = row['Team Name']
            is_random = row['Is Random Team'].lower() == 'yes'
            team_members = [member.strip() for member in row['Team Members'].split(',')]
            
            # Handle multiple email addresses properly
            contact_emails = [email.strip() for email in row['Contact Emails'].split(',') if email.strip()]
            
            target_team = row['Target Team']
            target_members = [member.strip() for member in row['Target Members'].split(',')]
            
            teams_data[team_name] = {
                'is_random': is_random,
                'team_members': team_members,
                'contact_emails': contact_emails,
                'target_team': target_team,
                'target_members': target_members
            }
    
    # Second pass: Send emails to each team
    for team_name, team_info in teams_data.items():
        # Create email subject and body
        subject = "Senior Assassin: FINAL Target Assignment"
        
        # Different message for random teams
        if team_info['is_random']:
            body = f"""Hello Team {team_name},

Please disregard the last email, your new targets have been assigned! 

TARGET TEAM: {team_info['target_team']}

TEAM MEMBERS: {', '.join(team_info['target_members'])}

Remember:
1. Official Senior Assassin start date is THURSDAY MORNING (4/24). Get ready!
2. Your team must eliminate TWO members of your target team
3. Another team is hunting YOU, but you won't know which one
4. The Rulebook is in the Instagram bio, DM us on Instagram if you have any confusions

Good luck and happy hunting!

- Senior Assassin Organizers
"""
        else:
            body = f"""Hello Team {team_name},

Please disregard the last email, your new targets have been assigned! 

TARGET TEAM: {team_info['target_team']}

TEAM MEMBERS: {', '.join(team_info['target_members'])}

Remember:
1. Official Senior Assassin start date is THURSDAY MORNING (4/24). Get ready!
2. Your team must eliminate TWO members of your target team
3. Another team is hunting YOU, but you won't know which one
4. The Rulebook is in the Instagram bio, DM us on Instagram if you have any confusions

Good luck and happy hunting!

- Senior Assassin Organizers
"""
        
        # Send the email to all contact emails for this team
        if team_info['contact_emails']:
            if send_email(team_info['contact_emails'], subject, body):
                print(f"Email sent to team: {team_name} ({', '.join(team_info['contact_emails'])})")
            else:
                print(f"Failed to send email to team: {team_name}")
        else:
            print(f"No contact emails found for team: {team_name}")
        
        # Add a small delay to avoid overwhelming the email server
        time.sleep(1)

def send_individual_emails(csv_file):
    """
    Read the CSV file and send individual emails to each person about their team and target
    """
    # Dictionary to store participant data
    teams_data = {}
    participant_emails = {}
    
    # First pass: Read all team data from CSV
    with open(csv_file, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            team_name = row['Team Name']
            is_random = row['Is Random Team'].lower() == 'yes'
            team_members = [member.strip() for member in row['Team Members'].split(',')]
            contact_emails = [email.strip() for email in row['Contact Emails'].split(',') if email.strip()]
            target_team = row['Target Team']
            target_members = [member.strip() for member in row['Target Members'].split(',')]
            
            # Store team data
            teams_data[team_name] = {
                'is_random': is_random,
                'team_members': team_members,
                'contact_emails': contact_emails,
                'target_team': target_team,
                'target_members': target_members
            }
            
            # Map contact emails to team members as best as possible
            for i, member in enumerate(team_members):
                if i < len(contact_emails):
                    participant_emails[member] = contact_emails[i]
                elif contact_emails:
                    # If fewer emails than members, use the last email
                    participant_emails[member] = contact_emails[-1]
    
    # Send emails to each individual with their team's info
    for team_name, team_info in teams_data.items():
        # Create email subject 
        subject = "Senior Assassin: Your Team and Target Assignment"
        
        # Send email to each contact email
        for email in team_info['contact_emails']:
            # Customize message
            body = f"""Hello,

Please disregard the last email, your new targets have been assigned! 

YOUR TEAM: {team_name}

YOUR TEAMMATES: {', '.join(team_info['team_members'])}

TARGET TEAM: {team_info['target_team']}

TARGET MEMBERS: {', '.join(team_info['target_members'])}

Remember:
1. Official Senior Assassin start date is THURSDAY MORNING (4/24). Get ready!
2. Your team must eliminate TWO members of your target team
3. Another team is hunting YOU, but you won't know which one
4. The Rulebook is in the Instagram bio, DM us on Instagram if you have any confusions

Good luck and happy hunting!

- Senior Assassin Organizers
"""
            
            # Send the email
            if send_email(email, subject, body):
                print(f"Email sent to: {email} (Team: {team_name})")
            else:
                print(f"Failed to send email to: {email}")
            
            # Add a small delay to avoid overwhelming the email server
            time.sleep(1)

if __name__ == "__main__":
    csv_file = "team_data.csv"  # Change this to the path of your CSV file
    
    # Choose one of these functions to run:
    
    # Option 1: Send one email to each team (to all contacts listed)
    read_csv_and_send_emails(csv_file)
    
    # Option 2: Send individual emails to each contact email
    # send_individual_emails(csv_file)