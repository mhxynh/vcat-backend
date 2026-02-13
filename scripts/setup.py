import subprocess
import sys
import os
import json

def run_command(command):
    try:
        result = subprocess.run(
            command, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            shell=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()

def check_aws_cli():
    print("🔍 Checking for AWS CLI...")
    success, version = run_command("aws --version")
    if success:
        print(f"✅ Found AWS CLI: {version}")
        return True
    else:
        print("❌ AWS CLI not found.")
        print("   -> Please install it here: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
        return False

def check_connection():
    print("\n☁️  Verifying AWS Connection...")
    success, output = run_command("aws sts get-caller-identity --output json")
    
    if success:
        data = json.loads(output)
        arn = data.get("Arn", "Unknown")
        user = arn.split("/")[-1]
        print(f"✅ SUCCESS! Connected as user: {user}")
        print(f"   Account ID: {data.get('Account')}")
        return True
    else:
        print("⚠️  Connection Failed.")
        return False

def configure_aws():
    print("\n⚙️  Starting AWS Configuration Wizard...")
    print("   (Have your Access Key ID and Secret Access Key ready from the CSV file)")
    try:
        # We use subprocess.call to let the user interact with the terminal directly
        subprocess.call("aws configure", shell=True)
        return True
    except KeyboardInterrupt:
        print("\n   Configuration cancelled.")
        return False

def main():
    print("========================================")
    print("   V-CAT ENVIRONMENT SETUP")
    print("========================================")
    
    # Step 1: Check Tooling
    if not check_aws_cli():
        sys.exit(1)

    # Step 2: Check if already connected
    if check_connection():
        print("\n🎉 You are all set! You don't need to do anything else.")
        sys.exit(0)

    # Step 3: Configure if needed
    print("\n❌ No valid credentials found (or session expired).")
    choice = input("   Do you want to configure AWS now? (y/n): ").lower()
    
    if choice == 'y':
        configure_aws()
        # Verify again
        if check_connection():
            print("\n🚀 Setup Complete! You are ready to code.")
        else:
            print("\n❌ Something went wrong. Please check your keys and try again.")
    else:
        print("   Okay, run this script again when you are ready.")

    print("\n📦 Installing Python dependencies...")
    subprocess.call("pip install -r requirements.txt", shell=True)
    print("✅ Dependencies installed.")

if __name__ == "__main__":
    main()
