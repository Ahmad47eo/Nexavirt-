# NEXA REALITY

**A lightweight computer laboratory inside Windows.**

NEXA REALITY is a free desktop app with simulated computer profiles and an optional integration with **QEMU** for launching real virtual machines. Simulated profiles and real VMs are clearly separated.

## First milestone

- Create and manage computer profiles
- Start and stop simulated computers
- Open a simulated terminal for each profile
- Save and restore profile snapshots
- Store user data outside the repository, in your Windows application-data folder
- Optional real QEMU VMs with separate QCOW2 virtual disks
- Choose a Linux ISO and launch the VM from ISO or its virtual disk
- Start real guests with a conservative 1024 MB RAM setting for low-memory PCs
- Use Python's standard library only (QEMU is a separate install)

## Requirements

- Windows 10 or 11
- Python 3.10+ (Tkinter included with the standard Windows installer)

## Run

Double-click `run_nexareality.bat`, or run:

```powershell
python nexareality.py
```

If Windows cannot find Python, install it from [python.org](https://www.python.org/downloads/windows/) and enable **Add python.exe to PATH**.

## Real VM support (QEMU)

1. Install a Windows build of QEMU from the [official QEMU downloads page](https://www.qemu.org/download/).
2. Start NEXA REALITY and click **Real QEMU VMs**.
3. Click **Create real VM**, give it a name, select a bootable x86-64 Linux `.iso`, and choose a virtual disk size (8–128 GB; 16 GB is a reasonable starting point).
4. The app creates a `disk.qcow2` file inside `%APPDATA%\\NexaReality\\real_vms\\<vm-name>\\` and launches QEMU with 1024 MB guest RAM.
5. Use **Launch from ISO** to boot an installer, or **Launch from disk** after an operating system has been installed.

If QEMU is not detected automatically, the app asks you to locate `qemu-system-x86_64.exe`. It also needs `qemu-img.exe`, normally in the same QEMU folder. The ISO must be downloaded separately. A lightweight Linux ISO is recommended for PCs with 4 GB system RAM. VM performance depends on your CPU, available RAM, QEMU build, and guest OS.

**Safety notes:** The app stores virtual disks in its own application-data folder and does not repartition or format the Windows drive. Do not select your real Windows disk as a VM disk. A real guest OS can still make changes inside its own virtual disk. Back up anything important before experimenting.

## Roadmap

- [x] Lightweight profile manager foundation
- [x] Simulated start/stop and terminal
- [x] JSON-based snapshots
- [ ] Profile resource settings
- [ ] Simulated private network between profiles
- [x] Optional QEMU integration (initial real-VM launcher)
