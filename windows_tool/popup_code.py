
    def show_success_popup(self, method, cert_file):
        popup = ctk.CTkToplevel(self)
        popup.title("Success!")
        popup.geometry("400x300")
        popup.resizable(False, False)
        
        # Center popup
        x = self.winfo_x() + (self.winfo_width()//2) - 200
        y = self.winfo_y() + (self.winfo_height()//2) - 150
        popup.geometry(f"+{x}+{y}")
        
        # Success Icon/Text
        ctk.CTkLabel(popup, text="✅", font=("Arial", 60)).pack(pady=(20, 10))
        ctk.CTkLabel(popup, text="Drive Wiped Successfully!", font=("Arial", 18, "bold")).pack(pady=5)
        
        # Details
        info_frame = ctk.CTkFrame(popup, fg_color="transparent")
        info_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(info_frame, text=f"Method: {method}", anchor="w").pack(fill="x")
        
        # Certificate Path (Clickable-ish look)
        cert_label = ctk.CTkEntry(info_frame, width=300)
        cert_label.insert(0, cert_file)
        cert_label.configure(state="readonly")
        cert_label.pack(pady=5)
        
        def open_folder():
            import os
            folder = os.path.dirname(os.path.abspath(cert_file))
            os.startfile(folder)
            
        def open_cert():
            import os
            os.startfile(cert_file)
            
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="Open Certificate", command=open_cert).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Open Folder", command=open_folder, fg_color="gray").pack(side="left", padx=10)
        
        popup.grab_set()  # Make modal
