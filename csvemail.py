import csv
import random
import re
from collections import defaultdict
import difflib
import math
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure your email credentials here
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "sbseniorassassin2025@gmail.com"
#SENDER_PASSWORD = ""  # Replace with actual password or use app password


def parse_names(name_string):
    """Parse names from a comma/and separated string."""
    if not name_string:
        return []
    # Replace 'and' with comma for consistent splitting
    name_string = name_string.replace(' and ', ', ')
    # Split by comma and strip whitespace
    names = [name.strip() for name in name_string.split(',')]
    # Remove empty names
    return [name for name in names if name]


def extract_first_name(name):
    """Extract first name from a full name."""
    return name.split()[0].lower() if name else ""


def names_match(name1, name2, threshold=0.7):
    """Check if two names might refer to the same person using fuzzy matching."""
    # If one name is just a first name and that matches with the first name of the other
    name1_first = extract_first_name(name1)
    name2_first = extract_first_name(name2)
    
    # If either name is just a single word/name
    if len(name1.split()) == 1 or len(name2.split()) == 1:
        # Check if the single name matches the first name of the other
        if name1_first == name2_first:
            return True
    
    # Otherwise use fuzzy string matching
    similarity = difflib.SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
    return similarity >= threshold


def read_registration_data(registration_csv):
    """Read team registration data from CSV and separate random pool participants."""
    teams = {}
    team_emails = defaultdict(list)  # Store all emails associated with each team
    individuals_to_team = {}
    random_pool = []  # Store participants who want to be in random teams
    
    # First pass - collect all entries
    entries = []
    with open(registration_csv, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            entries.append(row)
    
    # Group entries by team name, handling random pool separately
    team_entries = defaultdict(list)
    random_entries = []
    
    for entry in entries:
        team_name = entry['Team Name']
        
        # Check if this is a random pool entry
        if team_name.lower() == "random":
            random_entries.append(entry)
        elif team_name:  # Only process if team name exists
            team_entries[team_name].append(entry)
    
    # Process each team
    for team_name, team_entry_list in team_entries.items():
        all_members = []  # Keep as list to preserve original name formats
        paid_members = []
        emails = []
        phones = []
        
        # Combine information from all entries for this team
        for entry in team_entry_list:
            entry_members = parse_names(entry['Team Members'])
            entry_paid = parse_names(entry['Full Name(s)'])
            email = entry['Email'].strip()
            phone = entry['Phone Number'].strip()
            
            # Add all members from this entry
            all_members.extend(entry_members)
            
            # Add all paid members from this entry
            paid_members.extend(entry_paid)
            
            # Add email and phone if provided
            if email:
                emails.append(email)
            if phone:
                phones.append(phone)
        
        # Consolidate member lists to remove duplicates while handling name variations
        consolidated_members = []
        seen_first_names = set()
        
        # First add team members, checking for duplicates by first name
        for member in all_members:
            first_name = extract_first_name(member)
            if first_name and first_name not in seen_first_names:
                consolidated_members.append(member)
                seen_first_names.add(first_name)
            elif not any(names_match(member, existing) for existing in consolidated_members):
                consolidated_members.append(member)
        
        # Then add any paid members not already included
        for paid in paid_members:
            if not any(names_match(paid, member) for member in consolidated_members):
                consolidated_members.append(paid)
        
        # Create the consolidated team entry
        teams[team_name] = {
            'members': consolidated_members,
            'paid_members_raw': paid_members,
            'contact_emails': emails,
            'contact_phones': phones,
            'primary_email': emails[0] if emails else "",
            'primary_phone': phones[0] if phones else ""
        }
        
        # Map individuals to their team
        for member in consolidated_members:
            individuals_to_team[member.lower()] = team_name
        
        # Map all emails to this team for payment tracking
        for email in emails:
            team_emails[team_name].append(email.lower())
    
    # Process random pool entries
    for entry in random_entries:
        # Get name from either the Full Name or Team Members fields
        if entry['Full Name(s)']:
            names = parse_names(entry['Full Name(s)'])
        else:
            names = parse_names(entry['Team Members'])
        
        # Add each person to the random pool with their contact info
        for name in names:
            if name:  # Only add if name is not empty
                random_pool.append({
                    'name': name,
                    'email': entry['Email'].strip(),
                    'phone': entry['Phone Number'].strip(),
                    'paid': True  # Assume people in random pool have paid since they filled out the form
                })
    
    return teams, individuals_to_team, team_emails, random_pool


def create_random_teams(random_pool, team_size=3):
    """Create teams from the random pool of participants."""
    # Shuffle the random pool for randomness
    random.shuffle(random_pool)
    
    random_teams = {}
    # Keep track of participant-to-team mapping for notifications
    participant_team_map = {}
    
    # Calculate how many teams we need
    num_teams = math.ceil(len(random_pool) / team_size)
    
    for i in range(num_teams):
        team_name = f"Random Team {i+1}"
        team_members = []
        team_emails = []
        team_phones = []
        team_participants = []  # Store full participant objects
        
        # Get team_size participants or whatever is left for the last team
        start_idx = i * team_size
        end_idx = min(start_idx + team_size, len(random_pool))
        
        for j in range(start_idx, end_idx):
            participant = random_pool[j]
            team_members.append(participant['name'])
            
            # Save the participant-to-team mapping
            participant_team_map[participant['name']] = {
                'team_name': team_name,
                'email': participant['email'],
                'teammates': [p['name'] for p in random_pool[start_idx:end_idx] if p['name'] != participant['name']]
            }
            
            team_participants.append(participant)
            
            if participant['email'] and participant['email'] not in team_emails:
                team_emails.append(participant['email'])
            if participant['phone'] and participant['phone'] not in team_phones:
                team_phones.append(participant['phone'])
        
        # Create the team entry
        random_teams[team_name] = {
            'members': team_members,
            'paid_members_raw': team_members.copy(),  # Everyone in random pool is assumed to have paid
            'contact_emails': team_emails,
            'contact_phones': team_phones,
            'primary_email': team_emails[0] if team_emails else "",
            'primary_phone': team_phones[0] if team_phones else "",
            'amount_paid': len(team_members) * 5.5,  # Assuming $5.5 per person as in the original code
            'explicitly_paid': team_members.copy(),
            'covered_by_payment': [],
            'unpaid_members': [],
            'all_paid': True,  # Everyone in random pool is assumed to have paid
            'participants': team_participants  # Store complete participant objects
        }
    
    return random_teams, participant_team_map


def read_payment_data(payment_csv):
    """Read payment data from CSV."""
    payments = defaultdict(float)
    
    try:
        with open(payment_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Print header row to debug
            print(f"Payment CSV Headers: {reader.fieldnames}")
            
            for row in reader:
                email = row.get('Customer', '').strip().lower()
                if not email:
                    print("Warning: Missing email in payment record")
                    continue
                
                # Try different common field names for payment amount
                amount_fields = ['Gross Amount', 'Gross amount', 'Amount', 'Payment', 'Total', 'Gross', 'Price']
                amount = None
                
                for field in amount_fields:
                    if field in row and row[field]:
                        try:
                            # Remove currency symbols and commas
                            amount_str = row[field].strip().replace('$', '').replace(',', '')
                            amount = float(amount_str)
                            print(f"Successfully processed payment: {email} - ${amount}")
                            break
                        except ValueError:
                            print(f"Warning: Could not convert '{row[field]}' to float for {email}")
                
                if amount is not None:
                    payments[email] += amount
                else:
                    print(f"Warning: No valid payment amount found for {email}")
    
    except Exception as e:
        print(f"Error reading payment data: {str(e)}")
    
    return payments


def determine_payment_status(teams, payments, team_emails):
    """Determine who has paid and who hasn't based on payment amounts and Full Name entries."""
    # Assume $X per person (replace with actual amount)
    FEE_PER_PERSON = 5.5  # $5.50 per person
    
    for team_name, team_data in teams.items():
        # Check if this is one of our auto-created random teams (they're already marked as paid)
        if team_name.startswith("Random Team "):
            continue
            
        # Count total team members
        total_members = len(team_data['members'])
        
        # Calculate total amount paid across all team emails
        total_paid_amount = 0
        for email in team_emails[team_name]:
            amount = payments.get(email, 0)
            total_paid_amount += amount
            print(f"  Email {email} paid: ${amount:.2f}")
        
        team_data['amount_paid'] = total_paid_amount
        print(f"Team: {team_name}, Total paid: ${total_paid_amount:.2f}")
        print(f"  Team members: {', '.join(team_data['members'])}")
        print(f"  Paid members from form: {', '.join(team_data['paid_members_raw'])}")
        
        # Determine which members are explicitly paid using smart name matching
        paid_indices = []
        for i, member in enumerate(team_data['members']):
            # Check if this member matches any name in the paid_members list
            for paid in team_data['paid_members_raw']:
                if names_match(member, paid):
                    paid_indices.append(i)
                    print(f"  Member '{member}' matched with paid entry '{paid}'")
                    break
        
        # Calculate remaining payment after covering explicitly paid members
        explicitly_paid_count = len(paid_indices)
        remaining_payment = max(0, total_paid_amount - (explicitly_paid_count * FEE_PER_PERSON))
        
        # Calculate how many additional members can be covered
        additional_covered = int(remaining_payment / FEE_PER_PERSON)
        
        # Identify unpaid members
        unpaid_indices = [i for i in range(total_members) if i not in paid_indices]
        covered_by_payment = unpaid_indices[:additional_covered]
        still_unpaid = unpaid_indices[additional_covered:]
        
        # Get the actual unpaid members
        unpaid_members = [team_data['members'][i] for i in still_unpaid]
        
        # Update team data
        team_data['explicitly_paid'] = [team_data['members'][i] for i in paid_indices]
        team_data['covered_by_payment'] = [team_data['members'][i] for i in covered_by_payment]
        team_data['unpaid_members'] = unpaid_members
        team_data['all_paid'] = len(unpaid_members) == 0
        
        # Print detailed payment status
        total_paid_people = explicitly_paid_count + len(covered_by_payment)
        print(f"  Payment analysis: ${total_paid_amount:.2f} covers {total_paid_people} out of {total_members} members")
        print(f"  Explicitly paid members: {', '.join(team_data['explicitly_paid'])}")
        print(f"  Additional members covered by payment: {', '.join(team_data['covered_by_payment'])}")
        if unpaid_members:
            print(f"  Unpaid members: {', '.join(unpaid_members)}")
        else:
            print("  All members paid ✓")


def generate_target_assignments(teams):
    """Generate a circular chain of targets where each team targets exactly one other team,
    and each team is targeted by exactly one team."""
    # Only include teams where all members have paid
    eligible_teams = [team_name for team_name, team_data in teams.items() if team_data['all_paid']]
    print(f"\nTeams eligible for target assignments (all members paid): {len(eligible_teams)}")
    
    # Shuffle the teams to randomize assignments
    random.shuffle(eligible_teams)
    
    target_assignments = {}
    excluded_teams = [team_name for team_name in teams.keys() if team_name not in eligible_teams]
    
    if len(eligible_teams) < 2:
        print("Not enough eligible teams to assign targets (minimum 2 required)")
        return target_assignments, excluded_teams
        
    # Create a circular chain of targets
    for i in range(len(eligible_teams)):
        # The next team in the list is the target (or the first team if we're at the end)
        hunter_team = eligible_teams[i]
        target_team = eligible_teams[(i + 1) % len(eligible_teams)]
        target_assignments[hunter_team] = target_team
        
    return target_assignments, excluded_teams

def export_team_data_to_csv(teams, target_assignments, filename="team_data.csv"):
    """Export team information, target assignments, and contact emails to a CSV file."""
    print(f"\nExporting team data to {filename}...")
    
    # Prepare data for CSV - each row will represent a team
    csv_data = []
    
    for team_name, team_data in teams.items():
        # Get target team if one is assigned
        target_team = target_assignments.get(team_name, "No target assigned")
        
        # Get target members if there's a target team
        target_members = ""
        if target_team != "No target assigned":
            target_members = ", ".join(teams[target_team]['members'])
        
        # Format members as comma-separated string
        members = ", ".join(team_data['members'])
        
        # Format contact emails as comma-separated string
        contact_emails = ", ".join(team_data['contact_emails'])
        
        # Is this a random team?
        is_random = team_name.startswith("Random Team ")
        
        # Create row data
        row = {
            'Team Name': team_name,
            'Is Random Team': 'Yes' if is_random else 'No',
            'Team Members': members,
            'Contact Emails': contact_emails,
            'Primary Email': team_data['primary_email'],
            'All Paid': 'Yes' if team_data['all_paid'] else 'No',
            'Target Team': target_team,
            'Target Members': target_members
        }
        
        csv_data.append(row)
    
    # Write to CSV file
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        fieldnames = [
            'Team Name', 'Is Random Team', 'Team Members', 'Contact Emails',
            'Primary Email', 'All Paid', 'Target Team', 'Target Members'
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in csv_data:
            writer.writerow(row)
    
    print(f"Successfully exported data for {len(csv_data)} teams to {filename}")
    return filename


def export_email_log_to_csv(email_data, filename="email_log.csv"):
    """Export information about emails sent to a CSV file."""
    print(f"\nExporting email log data to {filename}...")
    
    # Write to CSV file
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        fieldnames = [
            'Hunter Team', 'Target Team', 'Target Members', 'Recipient Email'
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in email_data:
            writer.writerow(row)
    
    print(f"Successfully exported data for {len(email_data)} emails sent to {filename}")
    return filename


def main():
    # File paths - replace with actual file paths
    registration_csv = "contacts.csv"
    payment_csv = "payments.csv"
    
    print("Reading registration data...")
    # Read data and separate random pool entries
    teams, individuals_to_team, team_emails, random_pool = read_registration_data(registration_csv)
    
    print(f"\nFound {len(random_pool)} participants for random team assignment")
    
    # Create random teams from the pool
    email_data = []  # To track emails sent
    if random_pool:
        random_teams, participant_team_map = create_random_teams(random_pool)
        print(f"Created {len(random_teams)} random teams")
        
        # Add the random teams to our main teams dictionary
        teams.update(random_teams)
        
        # Update team_emails for payment tracking
        for team_name, team_data in random_teams.items():
            for email in team_data['contact_emails']:
                team_emails[team_name].append(email.lower())
            
    print("\nReading payment data...")
    payments = read_payment_data(payment_csv)
    print(f"Processed {len(payments)} payment records")
    
    print("\nDetermining payment status...")
    # Determine payment status for regular teams (random teams are already marked as paid)
    determine_payment_status(teams, payments, team_emails)
    
    # Print team information and payment status
    print("\n===== TEAM PAYMENT STATUS =====")
    for team_name, team_data in sorted(teams.items()):
        print(f"\nTeam: {team_name}")
        print(f"Members: {', '.join(team_data['members'])}")
        print(f"Contact email(s): {', '.join(team_data['contact_emails'])}")
        print(f"Contact phone(s): {', '.join(team_data['contact_phones'])}")
        print(f"Amount Paid: ${team_data['amount_paid']:.2f}")
        
        if team_data['unpaid_members']:
            print(f"UNPAID MEMBERS: {', '.join(team_data['unpaid_members'])}")
            print("⚠️ Team NOT eligible for target assignments due to unpaid members")
        else:
            print("All members paid ✓")
            print("✅ Team eligible for target assignments")
    
    
    # Generate target assignments
    target_assignments, excluded_teams = generate_target_assignments(teams)
    
    print("\n\n===== TARGET ASSIGNMENTS =====")
    if target_assignments:
        for hunter, target in target_assignments.items():
            print(f"Team '{hunter}' is hunting Team '{target}'")
        
    else:
        print("No target assignments generated. Need at least 2 eligible teams with all members paid.")
    
    if excluded_teams:
        print("\n===== EXCLUDED TEAMS (UNPAID MEMBERS) =====")
        for team in sorted(excluded_teams):
            unpaid = teams[team]['unpaid_members']
            print(f"Team: {team} - Unpaid: {', '.join(unpaid)}")
    
    # Print random team assignments specifically
    print("\n===== RANDOM TEAM ASSIGNMENTS =====")
    for team_name in sorted(teams.keys()):
        if team_name.startswith("Random Team "):
            print(f"\n{team_name}")
            print(f"Members: {', '.join(teams[team_name]['members'])}")
    
    # Export all team and target data to CSV
    export_team_data_to_csv(teams, target_assignments, "team_data.csv")
    
    # Export information about emails sent
    if email_data:
        export_email_log_to_csv(email_data, "email_log.csv")


if __name__ == "__main__":
    main()