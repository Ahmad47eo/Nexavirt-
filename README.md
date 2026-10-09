# NEXA REALITY

**A lightweight computer laboratory inside Windows.**

Nexa Reality is a free, experimental desktop app for creating and managing virtual computer *profiles*. The first milestone is a safe simulation layer; it does **not** pretend that a simulated profile is a real virtual machine.

## First milestone

- Create and manage computer profiles
- Start and stop simulated computers
- Open a simulated terminal for each profile
- Save and restore profile snapshots
- Store user data outside the repository, in your Windows application-data folder
- Use Python's standard library only (no paid APIs or extra packages)

## Requirements

- Windows 10 or 11
- Python 3.10+ (Tkinter included with the standard Windows installer)

## Run

Double-click `run_nexareality.bat`, or run:

```powershell
python nexareality.py
```

If Windows cannot find Python, install it from [python.org](https://www.python.org/downloads/windows/) and enable **Add python.exe to PATH**.

## Important

The initial version creates **simulated computer profiles**, not actual guest operating systems. Real VM support via QEMU is a later, optional phase. Keep this app's data folder separate from system files; the app is designed not to modify Windows settings or disks.

## Roadmap

- [x] Lightweight profile manager foundation
- [x] Simulated start/stop and terminal
- [x] JSON-based snapshots
- [ ] Profile resource settings
- [ ] Simulated private network between profiles
- [ ] Optional QEMU integration
