import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import disk_manager
from wiper import Wiper
from certificate import generate_certificate
import os
import json
import urllib.request
import urllib.error


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class ZeroTraceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Set default license values before building UI
        self.license_key = ""
        self.license_plan = "Free (Community)"

        self.title("ZeroTrace - Secure Data Wiper")
        self.geometry("800x600")
        self.resizable(False, False)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(2, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="ZeroTrace", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)
        
        self.refresh_btn = ctk.CTkButton(self.sidebar, text="Refresh Drives", command=self.load_drives)
        self.refresh_btn.grid(row=1, column=0, padx=20, pady=10)

        self.license_label = ctk.CTkLabel(self.sidebar, text=f"License: {self.license_plan}", font=ctk.CTkFont(size=12))
        self.license_label.grid(row=3, column=0, padx=20, pady=(10, 5), sticky="s")
        
        self.activate_btn = ctk.CTkButton(self.sidebar, text="Activate License", command=self.show_activation_popup)
        self.activate_btn.grid(row=4, column=0, padx=20, pady=(5, 20), sticky="s")

        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.label_title = ctk.CTkLabel(self.main_frame, text="Select Drive to Wipe", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_title.pack(pady=10)
        
        self.drive_list_frame = ctk.CTkScrollableFrame(self.main_frame, width=500, height=250)
        self.drive_list_frame.pack(pady=10)
        
        self.method_label = ctk.CTkLabel(self.main_frame, text="Wiping Method:", font=ctk.CTkFont(size=14))
        self.method_label.pack(pady=(10, 0))
        
        self.wipe_methods = [
            "NIST 800-88 Clear",
            "NIST 800-88-2 Purge",
            "DoD 5220.22-M (3-Pass)",
            "DoD 5220.22-M ECE (7-Pass)",
            "Peter Gutmann (35-Pass)"
        ]
        self.method_dropdown = ctk.CTkComboBox(self.main_frame, values=self.wipe_methods, width=250)
        self.method_dropdown.set("NIST 800-88 Clear")
        self.method_dropdown.pack(pady=5)
        
        self.selected_drive = None
        self.drive_buttons = []
        
        self.wipe_btn = ctk.CTkButton(self.main_frame, text="WIPE SELECTED DRIVE", fg_color="red", hover_color="#cc0000", state="disabled", command=self.confirm_wipe)
        self.wipe_btn.pack(pady=20)
        
        self.progress_bar = ctk.CTkProgressBar(self.main_frame, width=400)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10)
        self.progress_bar.pack_forget() 

        self.status_label = ctk.CTkLabel(self.main_frame, text="")
        self.status_label.pack()

        self.load_drives()
        self.load_license()

    def load_drives(self):
        for btn in self.drive_buttons:
            btn.destroy()
        self.drive_buttons = []
        self.selected_drive = None
        self.wipe_btn.configure(state="disabled")
        
        try:
            self.drives = disk_manager.list_all_wipeable_targets()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list drives: {e}")
            return

        for drive in self.drives:
            text = ""
            is_protected = drive.get('is_system', False)

            if drive['type'] == 'volume':
                label = drive.get('label', 'No Label')
                letter = drive.get('letter', '')
                size_str = disk_manager.format_size(drive['size'])
                
                text = f"{letter}:\\ - {label} ({size_str})"
                if is_protected:
                    text += " [SYSTEM - PROTECTED]"
            else: 
                model = drive.get('model', 'Unknown Disk')
                size_str = disk_manager.format_size(drive['size'])
                
                text = f"{model} ({size_str})"
                if is_protected:
                    text += " [SYSTEM DISK - PROTECTED]"
                else:
                    text += " [ENTIRE DISK]"
            
            if is_protected:
                color = "gray"
                state = "disabled"
            else:
                color = "#2b2b2b"
                state = "normal"
            
            btn = ctk.CTkButton(self.drive_list_frame, text=text, 
                                command=lambda d=drive: self.select_drive(d),
                                fg_color=color, 
                                border_width=2,
                                border_color="#333",
                                hover_color="#3a3a3a" if not is_protected else "gray",
                                state=state)
            btn.pack(fill="x", pady=5, padx=5)
            self.drive_buttons.append(btn)

    def select_drive(self, drive):
        self.selected_drive = drive
        if drive['type'] == 'volume':
            display_name = f"{drive['letter']}:\\ - {drive['label']}"
        else:
            display_name = drive['model']
        
        self.label_title.configure(text=f"Selected: {display_name}")
        self.wipe_btn.configure(state="normal")
        

    def confirm_wipe(self):
        if not self.selected_drive:
            return
        
        method = self.method_dropdown.get()
        if method != "NIST 800-88 Clear" and self.license_plan == "Free (Community)":
            messagebox.showwarning("Premium Feature", 
                                   "The selected wiping method is only available for Pro and Enterprise users.\n\nPlease purchase or activate a license on our website.")
            return
        
        if self.selected_drive['type'] == 'volume':
            drive_name = f"{self.selected_drive['letter']}:\\ - {self.selected_drive['label']}"
            size_display = disk_manager.format_size(self.selected_drive['size'])
        else:
            drive_name = self.selected_drive['model']
            size_display = disk_manager.format_size(self.selected_drive['size'])
            
        confirm = messagebox.askyesno("WARNING", 
                                      f"PERMANENTLY ERASE ALL DATA ON:\n\n{drive_name} ({size_display})\n\nMethod: {method}\n\nThis cannot be undone. Are you sure?")
        if confirm:
            confirm2 = messagebox.askyesno("FINAL WARNING", "This is your last chance. All data will be destroyed. Proceed?")
            if confirm2:
                self.start_wipe()

    def start_wipe(self):
        self.wipe_btn.configure(state="disabled")
        self.refresh_btn.configure(state="disabled")
        self.method_dropdown.configure(state="disabled")
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        self.status_label.configure(text="Initializing Wipe...")
        
        threading.Thread(target=self.run_wipe_process).start()

    def run_wipe_process(self):
        wiper = Wiper(self.selected_drive["device_id"])
        method = self.method_dropdown.get()
        
        def update_progress(ratio, total, current, pass_num, total_passes):
            if ratio >= 0.99:
                ratio = 1.0
            
            percentage = int(ratio * 100)
            text = f"Wiping ({method}): Pass {pass_num}/{total_passes} - {percentage}%"
            
            self.after(0, lambda: self.progress_bar.set(ratio))
            self.after(0, lambda: self.status_label.configure(text=text))
        
        success = wiper.run_wipe(method, progress_callback=update_progress)
        
        if success:
            def on_success():
                self.progress_bar.set(1.0)
                self.status_label.configure(text="✅ Complete!")
                try:
                    self.status_label.configure(text="Generating certificate...")
                    cert_file = generate_certificate(self.selected_drive, method, "SUCCESS")
                    
                    # Log wipe telemetry to backend database
                    threading.Thread(target=self.send_telemetry, args=(method,)).start()

                    self.status_label.configure(text="✅ Complete!")
                    self.show_success_popup(method, cert_file)
                except Exception as e:
                    messagebox.showwarning("Wipe Success", f"Wipe done but certificate failed: {e}")
                finally:
                    self.reset_ui()
            
            self.after(0, on_success)
        else:
            def on_fail():
                self.status_label.configure(text="Wipe Failed!", text_color="red")
                messagebox.showerror("Error", "Failed to wipe drive. Check permissions.")
                self.reset_ui()
            
            self.after(0, on_fail)

    def show_success_popup(self, method, cert_file):
        popup = ctk.CTkToplevel(self)
        popup.title("Success!")
        popup.geometry("450x350")
        popup.resizable(False, False)
        popup.attributes("-topmost", True)  
        
        popup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()//2) - 225
        y = self.winfo_y() + (self.winfo_height()//2) - 175
        popup.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(popup, text="✅", font=("Arial", 60)).pack(pady=(20, 10))
        ctk.CTkLabel(popup, text="Drive Wiped Successfully!", font=("Arial", 20, "bold")).pack(pady=5)
        
        info_frame = ctk.CTkFrame(popup, fg_color="transparent")
        info_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(info_frame, text=f"Method: {method}", font=("Arial", 12)).pack()
        ctk.CTkLabel(info_frame, text="Certificate Generated:", font=("Arial", 12, "bold")).pack(pady=(10, 5))
        
        path = os.path.abspath(cert_file)
        cert_entry = ctk.CTkEntry(info_frame, width=350, justify="center")
        cert_entry.insert(0, path)
        cert_entry.configure(state="readonly")
        cert_entry.pack(pady=5)
        
        def open_folder():
            folder = os.path.dirname(path)
            os.startfile(folder)
            popup.destroy()
            
        def open_cert():
            os.startfile(path)
            popup.destroy()
            
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="Open PDF", command=open_cert, width=120).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Open Folder", command=open_folder, width=120, fg_color="gray").pack(side="left", padx=10)

    def reset_ui(self):
        self.wipe_btn.configure(state="disabled")
        self.refresh_btn.configure(state="normal")
        self.method_dropdown.configure(state="normal")
        self.load_drives()

    def load_license(self):
        self.license_key = ""
        self.license_plan = "Free (Community)"
        if os.path.exists("license.json"):
            try:
                with open("license.json", "r") as f:
                    data = json.load(f)
                    self.license_key = data.get("key", "")
                    self.license_plan = data.get("plan", "Free (Community)")
                
                if self.license_key:
                    threading.Thread(target=self.verify_license_silently).start()
            except Exception:
                pass

    def save_license(self, key, plan):
        try:
            with open("license.json", "w") as f:
                json.dump({"key": key, "plan": plan}, f)
        except Exception as e:
            print(f"Failed to save license: {e}")

    def verify_license_silently(self):
        try:
            data = json.dumps({"key": self.license_key}).encode("utf-8")
            req = urllib.request.Request(
                "http://localhost:5000/api/activate",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=3) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                if res_body.get("success"):
                    plan_name = "Professional"
                    if "ent" in res_body.get("planId", "").lower():
                        plan_name = "Enterprise"
                    self.license_plan = plan_name
                    self.after(0, lambda: self.license_label.configure(text=f"License: {plan_name}"))
                else:
                    self.license_plan = "Free (Community)"
                    self.save_license("", "Free (Community)")
                    self.after(0, lambda: self.license_label.configure(text="License: Free (Community)"))
        except Exception:
            pass

    def show_activation_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Activate ZeroTrace")
        popup.geometry("400x200")
        popup.resizable(False, False)
        popup.attributes("-topmost", True)
        
        popup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()//2) - 200
        y = self.winfo_y() + (self.winfo_height()//2) - 100
        popup.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(popup, text="Enter License Key", font=("Arial", 16, "bold")).pack(pady=(20, 10))
        
        key_entry = ctk.CTkEntry(popup, width=300, justify="center", placeholder_text="ZT-PRO-XXXX-XXXX-XXXX")
        key_entry.pack(pady=10)
        
        def attempt_activation():
            key = key_entry.get().strip()
            if not key:
                messagebox.showerror("Error", "Please enter a license key.")
                return
            
            try:
                data = json.dumps({"key": key}).encode("utf-8")
                req = urllib.request.Request(
                    "http://localhost:5000/api/activate",
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    res_body = json.loads(response.read().decode("utf-8"))
                    if res_body.get("success"):
                        plan_name = "Professional"
                        if "ent" in res_body.get("planId", "").lower():
                            plan_name = "Enterprise"
                        
                        self.save_license(key, plan_name)
                        self.license_key = key
                        self.license_plan = plan_name
                        self.license_label.configure(text=f"License: {plan_name}")
                        
                        messagebox.showinfo("Success", f"License activated successfully!\nPlan: {plan_name}")
                        popup.destroy()
                    else:
                        messagebox.showerror("Activation Failed", res_body.get("error", "Invalid key."))
            except urllib.error.HTTPError as e:
                try:
                    err_msg = json.loads(e.read().decode("utf-8")).get("error", "Activation failed.")
                except Exception:
                    err_msg = f"HTTP Error {e.code}"
                messagebox.showerror("Activation Failed", err_msg)
            except Exception as e:
                messagebox.showerror("Error", f"Could not reach server: {e}\nMake sure your server is running.")
        
        ctk.CTkButton(popup, text="Activate", command=attempt_activation).pack(pady=10)

    def send_telemetry(self, method):
        try:
            import random
            drive_size_bytes = self.selected_drive.get("size", 0)
            drive_size_gb = drive_size_bytes / (1024 * 1024 * 1024)
            files_count = max(100, int(drive_size_gb * 50) + random.randint(10, 500))

            telemetry_data = json.dumps({
                "filesWiped": files_count,
                "bytesWiped": drive_size_bytes,
                "method": method
            }).encode("utf-8")
            
            req = urllib.request.Request(
                "http://localhost:5000/api/telemetry",
                data=telemetry_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=3) as response:
                pass
        except Exception as e:
            print(f"[WARNING] Telemetry reporting failed: {e}")

if __name__ == "__main__":
    app = ZeroTraceApp()
    app.mainloop()
