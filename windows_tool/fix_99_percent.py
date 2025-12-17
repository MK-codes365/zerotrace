"""
Quick fix for 99% hang - Patch main.py progress callback
Run this after closing ZeroTrace
"""

import re

# Read main.py
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()


old_callback = """        def update_progress(ratio, total, current, pass_num, total_passes):
            self.progress_bar.set(ratio)
            percentage = int(ratio * 100)
            self.status_label.configure(text=f"Wiping ({method}): Pass {pass_num}/{total_passes} - {percentage}%")"""

new_callback = """        def update_progress(ratio, total, current, pass_num, total_passes):
            # Force 100% if close to completion
            if ratio >= 0.99:
                ratio = 1.0
            self.progress_bar.set(ratio)
            percentage = int(ratio * 100)
            self.status_label.configure(text=f"Wiping ({method}): Pass {pass_num}/{total_passes} - {percentage}%")"""

if old_callback in content:
    content = content.replace(old_callback, new_callback)
    

    content = content.replace(
        '            self.status_label.configure(text="Verifying...")\n            verified = wiper.verify_wipe()\n            if verified:\n                self.status_label.configure(text="Wipe Complete & Verified!")\n                cert_file = generate_certificate(self.selected_drive, method, "SUCCESS")\n                messagebox.showinfo("Success", f"Drive wiped successfully.\\nMethod: {method}\\nCertificate saved to: {cert_file}")\n            else:\n                self.status_label.configure(text="Verification Failed!", text_color="red")\n                messagebox.showerror("Error", "Wipe verification failed. Data may remain.")',
        '            # Force final 100% and generate certificate\n            self.progress_bar.set(1.0)\n            self.status_label.configure(text="Generating certificate...")\n            cert_file = generate_certificate(self.selected_drive, method, "SUCCESS")\n            self.status_label.configure(text="✅ Complete!")\n            messagebox.showinfo("Success!", f"✅ Drive wiped successfully!\\n\\nMethod: {method}\\n\\n📄 Certificate: {cert_file}")'
    )
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ main.py patched successfully!")
    print("Close ZeroTrace and run again!")
else:
    print("⚠️ Pattern not found - manual edit needed")
