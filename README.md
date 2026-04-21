# Faculty Evaluation - Step by Step Guide

This guide is for Windows users.

## Step 1: Download the Files

1. Open the project page.
2. Click **Code**.
3. Click **Download ZIP**.
4. Extract the ZIP to a folder, for example: `C:\Faculty-Evaluation`

## Step 2: Install Python (Full Guide)

1. Go to: https://www.python.org/downloads/windows/
2. Click **Download Python 3.x**.
3. Run the downloaded installer.
4. On the first installer screen, check:
	- **Add Python to PATH**
5. Click **Install Now**.
6. Wait for installation to complete.
7. If you see **Disable path length limit**, click it.
8. Close the installer.

### Verify Python Installation

1. Press **Win + R**, type `cmd`, press Enter.
2. Run:

```bash
python --version
```

3. If version appears (example `Python 3.12.x`), installation is successful.

If it says Python is not recognized:
- Restart your PC and try again.
- Or reinstall Python and make sure **Add Python to PATH** is checked.

## Step 3: Install Requirements

1. Open Command Prompt in your project folder:
	- Go to the extracted folder in File Explorer.
	- Click the address bar, type `cmd`, then press Enter.
2. Run:

```bash
pip install -r requirements.txt
```

If `pip` is not recognized, run:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Step 4: Open CLI in Project Folder

If your Command Prompt is already open in the project folder, continue.

Otherwise:
1. Press **Win + R**.
2. Type `cmd`, press Enter.
3. Move to your project folder:

```bash
cd C:\Faculty-Evaluation
```

## Step 5: Run the Script

Run exactly:

```bash
python3 fe.py
```

If `python3` is not recognized on your Windows, use:

```bash
python fe.py
```

## What You Will Enter in Script

The script will ask for:
1. Username/ID
2. Password
3. Browser choice (Edge / Chrome / Firefox)
4. Rating option:
	- Very Good
	- Good
	- Average
	- Poor
	- Very Poor
5. Overall comments
6. Recommendations

## Note

At first run, browser initialization may take time because WebDriver may be downloaded automatically.
