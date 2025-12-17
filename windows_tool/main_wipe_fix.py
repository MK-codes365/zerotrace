    def run_wipe_process(self):
        """Run the wipe in background thread and generate certificate"""
        wiper = Wiper(self.selected_drive["device_id"])
        method = self.method_dropdown.get()
        
        def update_progress(ratio, total, current, pass_num, total_passes):
            # Force 100% if >= 0.99 to prevent hanging
            if ratio >= 0.99:
                ratio = 1.0
            self.progress_bar.set(ratio)
            percentage = int(ratio * 100)
            self.status_label.configure(text=f"Wiping ({method}): Pass {pass_num}/{total_passes} - {percentage}%")
        
        # Run wipe
        success = wiper.run_wipe(method, progress_callback=update_progress)
        
        # Always set to 100% when done
        self.progress_bar.set(1.0)
        self.status_label.configure(text="Generating certificate...")
        
        if success:
            # Generate certificate
            try:
                cert_file = generate_certificate(self.selected_drive, method, "SUCCESS")
                self.status_label.configure(text="✅ Complete!")
                messagebox.showinfo("Wipe Complete!", 
                                  f"✅ Drive wiped successfully!\n\n"
                                  f"Method: {method}\n"
                                  f"📄 Certificate: {cert_file}\n\n"
                                  f"PDF and JSON certificates generated!")
            except Exception as e:
                messagebox.showwarning("Certificate Error", 
                                     f"Wipe succeeded but certificate generation failed:\n{e}")
        else:
            self.status_label.configure(text="❌ Failed!", text_color="red")
            messagebox.showerror("Error", "Failed to wipe drive. Check console for details.")
            
        self.after(0, self.reset_ui)
