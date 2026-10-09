"""NEXA REALITY — lightweight virtual-computer lab prototype.

This first version manages simulated profiles only. It does not launch VMs,
change Windows settings, or execute commands entered in the simulated terminal.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from datetime import datetime
from pathlib import Path

APP_NAME = "NEXA REALITY"
DATA_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "NexaReality"
PROFILES_FILE = DATA_DIR / "profiles.json"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
REAL_VMS_DIR = DATA_DIR / "real_vms"

BG = "#0b1020"
PANEL = "#121a2d"
PANEL2 = "#17223a"
TEXT = "#edf3ff"
MUTED = "#93a4c2"
ACCENT = "#65e6c2"
BLUE = "#80aaff"
DANGER = "#ff8d9b"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class NexaRealityApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_NAME + " | Virtual Computer Lab")
        self.root.geometry("1000x650")
        self.root.minsize(760, 520)
        self.root.configure(bg=BG)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        REAL_VMS_DIR.mkdir(parents=True, exist_ok=True)
        self.real_vm_processes: dict[str, subprocess.Popen] = {}
        self.profiles = self.load_profiles()
        self.selected_id: str | None = None
        self.build_ui()
        self.refresh()

    def load_profiles(self) -> list[dict]:
        try:
            data = json.loads(PROFILES_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except (OSError, json.JSONDecodeError):
            pass
        return []

    def save_profiles(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        temp = PROFILES_FILE.with_suffix(".tmp")
        temp.write_text(json.dumps(self.profiles, indent=2), encoding="utf-8")
        temp.replace(PROFILES_FILE)

    def build_ui(self) -> None:
        top = tk.Frame(self.root, bg=BG, padx=24, pady=18)
        top.pack(fill="x")
        tk.Label(top, text="NEXA", bg=BG, fg=ACCENT,
                 font=("Segoe UI", 20, "bold")).pack(side="left")
        tk.Label(top, text=" REALITY", bg=BG, fg=TEXT,
                 font=("Segoe UI", 20, "bold")).pack(side="left")
        tk.Label(top, text="YOUR VIRTUAL COMPUTER LAB", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(side="right", pady=10)

        body = tk.Frame(self.root, bg=BG, padx=20, pady=6)
        body.pack(fill="both", expand=True)
        sidebar = tk.Frame(body, bg=PANEL, width=250, padx=14, pady=14)
        sidebar.pack(side="left", fill="y", padx=(0, 14))
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="COMPUTER PROFILES", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 10))
        self.profile_list = tk.Listbox(
            sidebar, bg=PANEL2, fg=TEXT, selectbackground="#2b4568",
            selectforeground=TEXT, relief="flat", borderwidth=0,
            highlightthickness=0, font=("Segoe UI", 10), activestyle="none"
        )
        self.profile_list.pack(fill="both", expand=True)
        self.profile_list.bind("<<ListboxSelect>>", self.on_select)
        self.make_button(sidebar, "+  New computer", self.new_profile, ACCENT, BG).pack(fill="x", pady=(12, 5))
        self.make_button(sidebar, "Delete selected", self.delete_profile, "#29364f", TEXT).pack(fill="x")
        self.make_button(sidebar, "Real QEMU VMs", self.open_real_vm_manager, BLUE, BG).pack(fill="x", pady=(12, 0))

        main = tk.Frame(body, bg=BG)
        main.pack(side="left", fill="both", expand=True)
        self.welcome = tk.Label(main, text="Welcome to your lab", bg=BG, fg=TEXT,
                                font=("Segoe UI", 21, "bold"))
        self.welcome.pack(anchor="w", pady=(8, 4))
        tk.Label(main, text="Create isolated profiles and experiment safely.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 18))

        stats = tk.Frame(main, bg=BG)
        stats.pack(fill="x", pady=(0, 16))
        self.total_value = self.stat_card(stats, "PROFILES", "0")
        self.running_value = self.stat_card(stats, "RUNNING", "0")
        self.snapshot_value = self.stat_card(stats, "SNAPSHOTS", "0")

        self.detail = tk.Frame(main, bg=PANEL, padx=20, pady=18)
        self.detail.pack(fill="both", expand=True)
        self.detail_title = tk.Label(self.detail, text="No computer selected",
                                     bg=PANEL, fg=TEXT, font=("Segoe UI", 16, "bold"))
        self.detail_title.pack(anchor="w")
        self.status_label = tk.Label(self.detail, text="Create a profile to begin.",
                                     bg=PANEL, fg=MUTED, font=("Segoe UI", 10))
        self.status_label.pack(anchor="w", pady=(7, 14))
        self.info_label = tk.Label(self.detail, text="",
                                   bg=PANEL, fg=MUTED, justify="left",
                                   font=("Consolas", 10), anchor="w")
        self.info_label.pack(fill="x", pady=(0, 14))
        actions = tk.Frame(self.detail, bg=PANEL)
        actions.pack(anchor="w")
        self.start_button = self.make_button(actions, "▶  Start", self.start_profile, ACCENT, BG)
        self.start_button.pack(side="left", padx=(0, 8))
        self.stop_button = self.make_button(actions, "■  Stop", self.stop_profile, "#29364f", TEXT)
        self.stop_button.pack(side="left", padx=(0, 8))
        self.make_button(actions, "⌘  Open terminal", self.open_terminal, "#29364f", TEXT).pack(side="left", padx=(0, 8))
        self.make_button(actions, "Snapshot", self.take_snapshot, "#29364f", TEXT).pack(side="left")

        footer = tk.Label(self.root,
            text="SIMULATED PROFILES + OPTIONAL REAL QEMU VMs  •  VM disks stay in your app-data folder",
            bg=BG, fg="#e7c778", font=("Segoe UI", 9, "bold"), pady=10)
        footer.pack(fill="x")

    def stat_card(self, parent: tk.Widget, title: str, value: str) -> tk.Label:
        card = tk.Frame(parent, bg=PANEL, padx=15, pady=12)
        card.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(card, text=title, bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        result = tk.Label(card, text=value, bg=PANEL, fg=ACCENT,
                          font=("Segoe UI", 20, "bold"))
        result.pack(anchor="w", pady=(3, 0))
        return result

    @staticmethod
    def make_button(parent: tk.Widget, text: str, command, bg: str, fg: str) -> tk.Button:
        return tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                         activebackground=bg, activeforeground=fg,
                         relief="flat", borderwidth=0, padx=12, pady=9,
                         cursor="hand2", font=("Segoe UI", 9, "bold"))

    def selected_profile(self) -> dict | None:
        return next((p for p in self.profiles if p["id"] == self.selected_id), None)

    def refresh(self) -> None:
        current = self.selected_id
        self.profile_list.delete(0, tk.END)
        for profile in self.profiles:
            mark = "●" if profile.get("running") else "○"
            self.profile_list.insert(tk.END, f"{mark}  {profile['name']}")
        if current:
            for index, profile in enumerate(self.profiles):
                if profile["id"] == current:
                    self.profile_list.selection_set(index)
                    self.profile_list.activate(index)
                    break
        running = sum(bool(p.get("running")) for p in self.profiles)
        snapshots = len(list(SNAPSHOTS_DIR.glob("*.json")))
        self.total_value.config(text=str(len(self.profiles)))
        self.running_value.config(text=str(running))
        self.snapshot_value.config(text=str(snapshots))
        self.update_detail()

    def update_detail(self) -> None:
        profile = self.selected_profile()
        if not profile:
            self.detail_title.config(text="No computer selected")
            self.status_label.config(text="Create a profile to begin.", fg=MUTED)
            self.info_label.config(text="Each profile is a safe simulation. Real VM support comes later.")
            self.start_button.config(state="disabled")
            self.stop_button.config(state="disabled")
            return
        self.detail_title.config(text=profile["name"])
        running = profile.get("running", False)
        self.status_label.config(
            text="● RUNNING — simulated computer" if running else "○ STOPPED — simulated computer",
            fg=ACCENT if running else MUTED
        )
        self.info_label.config(text=(
            f"Profile ID : {profile['id']}\n"
            f"Guest type : {profile.get('guest', 'Generic Linux (simulated)')}\n"
            f"Memory     : {profile.get('memory_mb', 512)} MB (label only in this prototype)\n"
            f"Created    : {profile.get('created', 'Unknown')}\n"
            f"Last event : {profile.get('last_event', 'Profile created')}"
        ))
        self.start_button.config(state="disabled" if running else "normal")
        self.stop_button.config(state="normal" if running else "disabled")

    def on_select(self, _event=None) -> None:
        selection = self.profile_list.curselection()
        if selection:
            self.selected_id = self.profiles[selection[0]]["id"]
            self.update_detail()

    def new_profile(self) -> None:
        name = simpledialog.askstring("New computer", "Give this computer a name:", parent=self.root)
        if not name or not name.strip():
            return
        name = name.strip()[:40]
        if any(p["name"].casefold() == name.casefold() for p in self.profiles):
            messagebox.showerror("Name already used", "Choose a different computer name.", parent=self.root)
            return
        profile = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "name": name,
            "guest": "Generic Linux (simulated)",
            "memory_mb": 512,
            "running": False,
            "created": now_text(),
            "last_event": "Profile created"
        }
        self.profiles.append(profile)
        self.selected_id = profile["id"]
        self.save_profiles()
        self.refresh()

    def delete_profile(self) -> None:
        profile = self.selected_profile()
        if not profile:
            return
        if not messagebox.askyesno("Delete profile", f"Delete the simulated profile '{profile['name']}'?", parent=self.root):
            return
        self.profiles = [p for p in self.profiles if p["id"] != profile["id"]]
        self.selected_id = None
        self.save_profiles()
        self.refresh()

    def start_profile(self) -> None:
        profile = self.selected_profile()
        if profile and not profile.get("running"):
            profile["running"] = True
            profile["last_event"] = "Simulated computer started at " + now_text()
            self.save_profiles()
            self.refresh()

    def stop_profile(self) -> None:
        profile = self.selected_profile()
        if profile and profile.get("running"):
            profile["running"] = False
            profile["last_event"] = "Simulated computer stopped at " + now_text()
            self.save_profiles()
            self.refresh()

    def open_terminal(self) -> None:
        profile = self.selected_profile()
        if not profile:
            messagebox.showinfo("Choose a computer", "Select or create a profile first.", parent=self.root)
            return
        window = tk.Toplevel(self.root)
        window.title(f"Simulated terminal — {profile['name']}")
        window.geometry("680x420")
        window.configure(bg="#050912")
        output = tk.Text(window, bg="#050912", fg=ACCENT, insertbackground=TEXT,
                         font=("Consolas", 10), relief="flat", padx=12, pady=12,
                         wrap="word", height=18)
        output.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        output.insert("end", f"NEXA REALITY SIMULATED TERMINAL\nComputer: {profile['name']}\n")
        output.insert("end", "This terminal does not execute Windows or guest OS commands.\n\n")
        entry = tk.Entry(window, bg=PANEL2, fg=TEXT, insertbackground=TEXT,
                         font=("Consolas", 10), relief="flat")
        entry.pack(fill="x", padx=10, pady=10)
        entry.focus_set()

        def submit(_event=None):
            command = entry.get().strip()
            if not command:
                return
            entry.delete(0, "end")
            output.insert("end", f"simulated@{profile['name'].replace(' ', '-').lower()}:~$ {command}\n")
            answers = {
                "help": "Available demo commands: help, status, date, files, clear, exit",
                "status": f"Profile: {profile['name']} | State: {'running' if profile.get('running') else 'stopped'}",
                "date": now_text(),
                "files": "Demo filesystem: /home/user  /home/user/notes.txt  /etc/nexa-release",
                "clear": "__CLEAR__",
                "exit": "__EXIT__"
            }
            answer = answers.get(command.lower(), "Command not found in the simulated terminal. Type 'help'.")
            if answer == "__CLEAR__":
                output.delete("1.0", "end")
            elif answer == "__EXIT__":
                window.destroy()
                return
            else:
                output.insert("end", answer + "\n")
            output.see("end")

        entry.bind("<Return>", submit)


    @staticmethod
    def find_qemu_program(program: str) -> str | None:
        found = shutil.which(program)
        if found:
            return found
        candidates = [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "qemu" / program,
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "QEMU" / program,
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "qemu" / program,
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "QEMU" / program,
        ]
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
        return None

    def open_real_vm_manager(self) -> None:
        window = tk.Toplevel(self.root)
        window.title("NEXA REALITY — Real QEMU VMs")
        window.geometry("720x460")
        window.minsize(580, 360)
        window.configure(bg=BG)
        tk.Label(window, text="REAL VIRTUAL MACHINES", bg=BG, fg=TEXT,
                 font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=18, pady=(16, 4))
        tk.Label(window, text="These use QEMU and a real virtual disk. On this PC, start with 1024 MB RAM.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=(0, 12))
        listing = tk.Listbox(window, bg=PANEL, fg=TEXT, selectbackground="#2b4568",
                             relief="flat", borderwidth=0, highlightthickness=0,
                             font=("Segoe UI", 10), activestyle="none")
        listing.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        vm_records: list[tuple[Path, dict]] = []

        def reload_list(select_path: str | None = None) -> None:
            listing.delete(0, tk.END)
            vm_records.clear()
            for meta_path in sorted(REAL_VMS_DIR.glob("*/vm.json")):
                try:
                    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
                    if metadata.get("disk_path") and Path(metadata["disk_path"]).is_file():
                        vm_records.append((meta_path.parent, metadata))
                        listing.insert(tk.END, f"{metadata.get('name', meta_path.parent.name)}   •   {metadata.get('disk_size_gb', 16)} GB disk")
                except (OSError, json.JSONDecodeError, TypeError):
                    continue
            if vm_records:
                target = next((i for i, (folder, _) in enumerate(vm_records)
                               if select_path and str(folder) == select_path), 0)
                listing.selection_set(target)
                listing.activate(target)

        def selected_record():
            selection = listing.curselection()
            if not selection:
                messagebox.showinfo("Choose a VM", "Select a real VM first.", parent=window)
                return None
            return vm_records[selection[0]]

        def launch_selected(boot_iso: bool) -> None:
            record = selected_record()
            if record:
                self.launch_real_vm(record[0], record[1], boot_iso=boot_iso, parent=window)

        def open_folder() -> None:
            record = selected_record()
            if not record:
                return
            try:
                os.startfile(str(record[0]))
            except (AttributeError, OSError) as exc:
                messagebox.showerror("Cannot open folder", str(exc), parent=window)

        def create_and_refresh() -> None:
            folder = self.create_real_vm()
            if folder:
                reload_list(str(folder))

        controls = tk.Frame(window, bg=BG)
        controls.pack(fill="x", padx=18, pady=(0, 16))
        self.make_button(controls, "+ Create real VM", create_and_refresh, ACCENT, BG).pack(side="left", padx=(0, 8))
        self.make_button(controls, "Launch from ISO", lambda: launch_selected(True), BLUE, BG).pack(side="left", padx=(0, 8))
        self.make_button(controls, "Launch from disk", lambda: launch_selected(False), "#29364f", TEXT).pack(side="left", padx=(0, 8))
        self.make_button(controls, "Open VM folder", open_folder, "#29364f", TEXT).pack(side="left")
        reload_list()

    def create_real_vm(self) -> Path | None:
        qemu = self.find_qemu_program("qemu-system-x86_64.exe") or self.find_qemu_program("qemu-system-x86_64")
        if not qemu:
            qemu = filedialog.askopenfilename(
                parent=self.root, title="Locate QEMU emulator",
                filetypes=[("QEMU emulator", "qemu-system-x86_64.exe"), ("Executable files", "*.exe"), ("All files", "*.*")]
            )
            if not qemu:
                messagebox.showinfo(
                    "QEMU is required",
                    "Install QEMU for Windows first, then try again. The app does not download or bundle QEMU.\n\n"
                    "Official QEMU download page: https://www.qemu.org/download/",
                    parent=self.root
                )
                return None
        qemu_path = Path(qemu)
        qemu_img = self.find_qemu_program("qemu-img.exe") or self.find_qemu_program("qemu-img")
        if not qemu_img:
            sibling = qemu_path.with_name("qemu-img.exe")
            if sibling.is_file():
                qemu_img = str(sibling)
        if not qemu_img:
            messagebox.showerror(
                "QEMU disk tool not found",
                "Could not find qemu-img.exe. It is normally in the same QEMU installation folder as qemu-system-x86_64.exe.",
                parent=self.root
            )
            return None

        name = simpledialog.askstring("Create real VM", "Name this virtual machine:", parent=self.root)
        if not name or not name.strip():
            return None
        name = name.strip()[:40]
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_") or "NexaVM"
        folder = REAL_VMS_DIR / safe_name
        if folder.exists():
            messagebox.showerror("Name already exists", "A VM with this folder name already exists. Choose another name.", parent=self.root)
            return None

        iso = filedialog.askopenfilename(
            parent=self.root, title="Choose a bootable Linux ISO",
            filetypes=[("ISO images", "*.iso"), ("All files", "*.*")]
        )
        if not iso:
            return None
        if not Path(iso).is_file() or Path(iso).suffix.lower() != ".iso":
            messagebox.showerror("Invalid ISO", "Choose an existing .iso file.", parent=self.root)
            return None
        disk_size = simpledialog.askinteger(
            "Virtual disk size", "Virtual disk maximum size in GB (8–128):",
            initialvalue=16, minvalue=8, maxvalue=128, parent=self.root
        )
        if disk_size is None:
            return None

        try:
            folder.mkdir(parents=True, exist_ok=False)
            disk_path = folder / "disk.qcow2"
            result = subprocess.run(
                [qemu_img, "create", "-f", "qcow2", str(disk_path), f"{disk_size}G"],
                capture_output=True, text=True, timeout=120, check=False
            )
            if result.returncode != 0:
                raise RuntimeError((result.stderr or result.stdout or "qemu-img failed").strip())
            metadata = {
                "name": name, "qemu_path": str(qemu_path), "qemu_img_path": str(qemu_img),
                "iso_path": str(Path(iso).resolve()), "disk_path": str(disk_path.resolve()),
                "disk_size_gb": disk_size, "memory_mb": 1024, "created": now_text(),
                "note": "Real QEMU VM. Guest RAM is 1024 MB; virtual disk is stored in this VM folder."
            }
            (folder / "vm.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
            messagebox.showerror("VM creation failed", f"Could not create the virtual disk.\n\n{exc}", parent=self.root)
            return None

        messagebox.showinfo(
            "Real VM created",
            f"Created a real {disk_size} GB virtual disk for '{name}'.\n\n"
            "The disk is a virtual file; it does not repartition your Windows drive. "
            "The VM will start with 1024 MB RAM. Performance depends on QEMU and your PC.",
            parent=self.root
        )
        self.launch_real_vm(folder, metadata, boot_iso=True, parent=self.root)
        return folder

    def launch_real_vm(self, folder: Path, metadata: dict, boot_iso: bool, parent=None) -> None:
        qemu = metadata.get("qemu_path")
        if not qemu or not Path(qemu).is_file():
            qemu = self.find_qemu_program("qemu-system-x86_64.exe") or self.find_qemu_program("qemu-system-x86_64")
        disk = Path(metadata.get("disk_path", ""))
        iso = Path(metadata.get("iso_path", ""))
        if not qemu or not Path(qemu).is_file():
            messagebox.showerror("QEMU not found", "QEMU is missing. Install it or choose its executable when creating a VM.", parent=parent or self.root)
            return
        if not disk.is_file():
            messagebox.showerror("Virtual disk missing", f"Could not find the VM disk:\n{disk}", parent=parent or self.root)
            return
        if boot_iso and not iso.is_file():
            messagebox.showerror("ISO missing", f"Could not find the ISO file:\n{iso}\n\nChoose Launch from disk if an OS is already installed.", parent=parent or self.root)
            return

        key = str(folder.resolve())
        running = self.real_vm_processes.get(key)
        if running and running.poll() is None:
            messagebox.showinfo("VM already running", "This VM is already running.", parent=parent or self.root)
            return
        command = [
            str(qemu), "-name", str(metadata.get("name", folder.name)),
            "-machine", "q35", "-m", str(int(metadata.get("memory_mb", 1024))),
            "-smp", "1", "-drive", f"file={disk},format=qcow2,if=virtio",
            "-boot", "order=d" if boot_iso else "order=c",
            "-nic", "user,model=virtio-net-pci"
        ]
        if boot_iso:
            command.extend(["-cdrom", str(iso)])
        log_path = folder / "qemu.log"
        try:
            with log_path.open("a", encoding="utf-8", errors="replace") as log:
                log.write(f"\n[{now_text()}] Launching: {command!r}\n")
                process = subprocess.Popen(
                    command, cwd=str(Path(qemu).parent), stdout=log, stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL, shell=False
                )
            self.real_vm_processes[key] = process
            self.root.after(1800, lambda: self.check_real_vm_start(process, log_path, parent))
        except OSError as exc:
            messagebox.showerror("Could not launch QEMU", str(exc), parent=parent or self.root)

    def check_real_vm_start(self, process: subprocess.Popen, log_path: Path, parent=None) -> None:
        if process.poll() is not None:
            try:
                log_text = log_path.read_text(encoding="utf-8", errors="replace")[-2500:]
            except OSError:
                log_text = "(No QEMU log was available.)"
            messagebox.showerror(
                "QEMU stopped immediately",
                f"QEMU exited with code {process.returncode}. Check the log below:\n\n{log_text}",
                parent=parent or self.root
            )
        else:
            messagebox.showinfo(
                "QEMU launched",
                "QEMU is running. A separate VM window should be open.\n\n"
                "For your 4 GB PC, keep the guest at 1024 MB RAM and close other heavy apps.",
                parent=parent or self.root
            )

    def take_snapshot(self) -> None:
        profile = self.selected_profile()
        if not profile:
            messagebox.showinfo("Choose a computer", "Select a profile first.", parent=self.root)
            return
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in profile["name"])
        path = SNAPSHOTS_DIR / f"{safe_name}-{stamp}.json"
        snapshot = {"snapshot_time": now_text(), "profile": dict(profile)}
        try:
            path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Snapshot failed", str(exc), parent=self.root)
            return
        profile["last_event"] = "Snapshot saved at " + now_text()
        self.save_profiles()
        self.refresh()
        messagebox.showinfo("Snapshot saved", f"Saved snapshot:\n{path}", parent=self.root)


def main() -> None:
    root = tk.Tk()
    NexaRealityApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
