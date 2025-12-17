import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import disk_manager
from wiper import Wiper
from certificate import generate_certificate
import os

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class ZeroTraceApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ZeroTrace - Secure Data Wiper")
        self.geometry("800x600")
        self.resizable(False, False)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="ZeroTrace", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)
        
        self.refresh_btn = ctk.CTkButton(self.sidebar, text="Refresh Drives", command=self.load_drives)
        self.refresh_btn.grid(row=1, column=0, padx=20, pady=10)

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
        
        if self.selected_drive['type'] == 'volume':
            drive_name = f"{self.selected_drive['letter']}:\\ - {self.selected_drive['label']}"
            size_display = disk_manager.format_size(self.selected_drive['size'])
        else:
            drive_name = self.selected_drive['model']
            size_display = disk_manager.format_size(self.selected_drive['size'])
            
        method = self.method_dropdown.get()
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

if __name__ == "__main__":
    app = ZeroTraceApp()
    app.mainloop()
