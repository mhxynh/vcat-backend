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

def check_tool(name, command, install_link):
    print(f"🔍 Checking for {name}...")
    success, version = run_command(command)
    if success:
        print(f"✅ Found {name}: {version.splitlines()[0]}")
        return True
    else:
        print(f"❌ {name} not found.")
        print(f"   -> Please install it here: {install_link}")
        return False

def check_docker():
    print("🔍 Checking for Docker...")
    success, _ = run_command("docker ps")
    if success:
        print("✅ Docker is running.")
        return True
    else:
        print("❌ Docker is NOT running or not installed.")
        print("   -> Open Docker Desktop before running the backend.")
        return False

def check_connection():
    print("\n☁️  Verifying AWS Connection...")
    success, output = run_command("aws sts get-caller-identity --output json")
    if success:
        data = json.loads(output)
        print(f"✅ SUCCESS! Connected as user: {data.get('Arn').split('/')[-1]}")
        return True
    return False

def setup_venv():
    if not os.path.exists("venv"):
        print("\n📦 Creating Virtual Environment (venv)...")
        run_command("python -m venv venv")
    
    print("📦 Installing/Updating Python dependencies...")
    pip_cmd = "venv\\Scripts\\pip" if os.name == "nt" else "venv/bin/pip"
    run_command(f"{pip_cmd} install -r requirements.txt")
    print("✅ Python dependencies installed in venv.")

def main():
    print("========================================")
    print("   V-CAT FULL STACK ENVIRONMENT SETUP")
    print("========================================")
    
    # 1. Check Fundamental Tools
    tools = [
        ("AWS CLI", "aws --version", "https://aws.amazon.com/cli/"),
        ("AWS SAM CLI", "sam --version", "https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"),
        ("Node.js", "node --version", "https://nodejs.org/"),
    ]
    
    all_tools_present = True
    for name, cmd, link in tools:
        if not check_tool(name, cmd, link):
            all_tools_present = False

    # 2. Check Docker (Mandatory for Backend)
    if not check_docker():
        all_tools_present = False

    if not all_tools_present:
        print("\n🛑 Setup incomplete. Please install missing tools and try again.")
        sys.exit(1)

    # 3. Handle Python Venv & Dependencies
    setup_venv()

    # 4. Check AWS Session
    if not check_connection():
        print("\n❌ No valid AWS credentials found.")
        choice = input("   Do you want to run 'aws configure' now? (y/n): ").lower()
        if choice == 'y':
            subprocess.call("aws configure", shell=True)
            if not check_connection():
                print("❌ Still unable to connect. Check your keys.")
    
    print("\n========================================")
    print("🚀 SETUP COMPLETE! You are ready to develop.")
    print("   - Backend: run 'sam build && sam local start-api'")
    print("   - Frontend: run 'npm install' then 'npm start'")
    print("========================================")

if __name__ == "__main__":
    main()