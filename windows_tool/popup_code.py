import customtkinter as ctk
import os

def show_success_popup(parent, method, cert_file):
    popup = ctk.CTkToplevel(parent)
    popup.title("Success!")
    popup.geometry("400x300")
    popup.resizable(False, False)
    
    # Center popup relative to parent window
    x = parent.winfo_x() + (parent.winfo_width()//2) - 200
    y = parent.winfo_y() + (parent.winfo_height()//2) - 150
    popup.geometry(f"+{x}+{y}")
    
    # Success Icon/Text
    ctk.CTkLabel(popup, text="✅", font=("Arial", 60)).pack(pady=(20, 10))
    ctk.CTkLabel(popup, text="Drive Wiped Successfully!", font=("Arial", 18, "bold")).pack(pady=5)
    
    # Details Frame
    info_frame = ctk.CTkFrame(popup, fg_color="transparent")
    info_frame.pack(pady=10, padx=20, fill="x")
    
    ctk.CTkLabel(info_frame, text=f"Method: {method}", anchor="w").pack(fill="x")
    
    # Certificate Path Display
    cert_label = ctk.CTkEntry(info_frame, width=300)
    cert_label.insert(0, cert_file)
    cert_label.configure(state="readonly")
    cert_label.pack(pady=5)
    
    def open_folder():
        folder = os.path.dirname(os.path.abspath(cert_file))
        os.startfile(folder)
        popup.destroy()
        
    def open_cert():
        os.startfile(cert_file)
        popup.destroy()
        
    btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
    btn_frame.pack(pady=20)
    
    ctk.CTkButton(btn_frame, text="Open Certificate", command=open_cert).pack(side="left", padx=10)
    ctk.CTkButton(btn_frame, text="Open Folder", command=open_folder, fg_color="gray").pack(side="left", padx=10)
    
    popup.grab_set()  # Make modal
