import os
import glob

base_dir = r"D:\GISLab\Prog-For-GIS\CourseProj"
scripts = glob.glob(os.path.join(base_dir, "scripts", "*.py")) + glob.glob(os.path.join(base_dir, "netlogo", "*.py"))
old_root = r"C:\Users\sathv\.gemini\antigravity\scratch\nedumangad_epidemic_abm"

for s in scripts:
    with open(s, "r", encoding="utf-8") as f:
        text = f.read()

    new_text = text.replace(old_root, base_dir)
    if new_text != text:
        with open(s, "w", encoding="utf-8") as f:
            f.write(new_text)
        print("Updated path to D:\\GISLab in:", os.path.basename(s))
