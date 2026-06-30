import customtkinter as ctk
import os

def show_success_popup(parent, method, cert_file):
    popup = ctk.CTkToplevel(parent)
    popup.title("Success!")
    popup.geometry("450x350")
    popup.resizable(False, False)
    popup.attributes("-topmost", True)  
    
    popup.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width()//2) - 225
    y = parent.winfo_y() + (parent.winfo_height()//2) - 175
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
    
    popup.grab_set()  # Make modal
