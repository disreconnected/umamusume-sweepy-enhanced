import json
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

# YEAR MAPPING FUNCTION
YEAR_MAP = {
    "junior year": "First Year",
    "classic year": "Second Year",
    "senior year": "Third Year",
    "junior": "First Year",
    "classic": "Second Year",
    "senior": "Third Year"
}

def normalize_name(name):
    """Strip all spaces, punctuation, dashes, and quotes to normalize race names."""
    if not name:
        return ""
    return re.sub(r'[^a-zA-Z0-9]', '', name).lower()

class ConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("uma.moe to uma.guide Agenda Converter")
        self.geometry("700x520")
        self.minsize(650, 480)
        
        # Load local database
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "races_database.json")
        self.races_db = []
        self.db_lookup = {}
        self.load_database()
        
        # UI Setup
        self.setup_ui()
        
    def load_database(self):
        if not os.path.exists(self.db_path):
            messagebox.showerror("Error", f"Database file races_database.json not found at {self.db_path}!")
            return
            
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                self.races_db = json.load(f)
                
            # Build lookup keyed by (normalized_name, year, turn)
            for race in self.races_db:
                key = (normalize_name(race["raceName"]), race["year"], race["turn"])
                self.db_lookup[key] = race
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load races database: {e}")

    def setup_ui(self):
        # Main Frame with padding
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Styling
        style = ttk.Style()
        style.configure("TButton", font=("Segoe UI", 9))
        style.configure("TLabel", font=("Segoe UI", 9))
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), foreground="white", background="#4CAF50")
        
        # Header
        header = ttk.Label(main_frame, text="Uma Musume Agenda Plan Converter", style="Header.TLabel")
        header.grid(row=0, column=0, columnspan=3, pady=(0, 15), sticky="w")
        
        # 1. Input File Selection
        ttk.Label(main_frame, text="Input JSON file (from uma.moe):").grid(row=1, column=0, sticky="w", pady=5)
        self.input_entry = ttk.Entry(main_frame, width=50)
        self.input_entry.grid(row=2, column=0, columnspan=2, sticky="ew", padx=(0, 5), pady=5)
        ttk.Button(main_frame, text="Browse...", command=self.browse_input).grid(row=2, column=2, sticky="ew", pady=5)
        
        # 2. Output Folder Selection
        ttk.Label(main_frame, text="Output Folder:").grid(row=3, column=0, sticky="w", pady=5)
        self.output_dir_entry = ttk.Entry(main_frame, width=50)
        self.output_dir_entry.grid(row=4, column=0, columnspan=2, sticky="ew", padx=(0, 5), pady=5)
        ttk.Button(main_frame, text="Browse...", command=self.browse_output_dir).grid(row=4, column=2, sticky="ew", pady=5)
        
        # 3. Output Filename
        ttk.Label(main_frame, text="Output Filename:").grid(row=5, column=0, sticky="w", pady=5)
        self.output_file_entry = ttk.Entry(main_frame, width=50)
        self.output_file_entry.grid(row=6, column=0, columnspan=2, sticky="ew", padx=(0, 5), pady=5)
        
        # 4. Conversion Action Button
        self.convert_btn = ttk.Button(main_frame, text="Convert Agenda", command=self.convert_agenda)
        self.convert_btn.grid(row=7, column=0, columnspan=3, pady=15, sticky="ew")
        
        # 5. Log area
        ttk.Label(main_frame, text="Log Console:").grid(row=8, column=0, sticky="w", pady=(5, 2))
        self.log_area = ScrolledText(main_frame, height=10, font=("Consolas", 9), state=tk.DISABLED)
        self.log_area.grid(row=9, column=0, columnspan=3, sticky="nsew", pady=5)
        
        # Grid configurations to make it responsive
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=0)
        main_frame.columnconfigure(2, weight=0)
        main_frame.rowconfigure(9, weight=1)
        
        # Default output directory as Downloads
        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        if os.path.exists(downloads_dir):
            self.output_dir_entry.insert(0, downloads_dir)
            
    def browse_input(self):
        initial_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()
            
        filename = filedialog.askopenfilename(
            title="Select uma.moe exported JSON file",
            initialdir=initial_dir,
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if filename:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, filename)
            
            # Suggest output filename
            basename = os.path.basename(filename)
            suggested_name = "converted-" + basename
            self.output_file_entry.delete(0, tk.END)
            self.output_file_entry.insert(0, suggested_name)
            
            # Suggest output directory if entry is empty
            if not self.output_dir_entry.get():
                self.output_dir_entry.insert(0, os.path.dirname(filename))
                
    def browse_output_dir(self):
        initial_dir = self.output_dir_entry.get() or os.getcwd()
        folder = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=initial_dir
        )
        if folder:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, folder)
            
    def log(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
        
    def clear_log(self):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)

    def convert_agenda(self):
        input_path = self.input_entry.get().strip()
        output_dir = self.output_dir_entry.get().strip()
        output_filename = self.output_file_entry.get().strip()
        
        if not input_path:
            messagebox.showwarning("Warning", "Please select an input JSON file first.")
            return
        if not os.path.exists(input_path):
            messagebox.showerror("Error", f"Input file does not exist:\n{input_path}")
            return
        if not output_dir:
            messagebox.showwarning("Warning", "Please select an output folder.")
            return
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create output folder:\n{output_dir}\nError: {e}")
                return
        if not output_filename:
            messagebox.showwarning("Warning", "Please specify an output filename.")
            return
            
        self.clear_log()
        self.log(f"Starting conversion of {os.path.basename(input_path)}...")
        
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                moe_races = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse input file JSON:\n{e}")
            self.log(f"FAILED: JSON parse error in {input_path}")
            return
            
        if not isinstance(moe_races, list):
            messagebox.showerror("Error", "Invalid file format: Top-level structure must be a JSON array.")
            self.log("FAILED: Expected list at root.")
            return
            
        converted_races = []
        matched_count = 0
        unmatched_count = 0
        
        for idx, moe_race in enumerate(moe_races):
            race_name = moe_race.get("raceName", "Unknown")
            turn = moe_race.get("turn", "Unknown")
            raw_year = moe_race.get("year", "Unknown")
            
            # Map year representation
            mapped_year = YEAR_MAP.get(raw_year.lower(), raw_year)
            
            # Search in our database
            lookup_key = (normalize_name(race_name), mapped_year, turn)
            db_match = self.db_lookup.get(lookup_key)
            
            if db_match:
                # Successfully matched: use full db entry
                converted_races.append({
                    "raceName": db_match["raceName"],
                    "grade": db_match["grade"],
                    "year": db_match["year"],  # Contains the correct First Year/Second Year/Third Year
                    "turn": db_match["turn"],
                    "type": db_match["type"],
                    "location": db_match["location"],
                    "length": db_match["length"],
                    "lengthM": db_match["lengthM"]
                })
                matched_count += 1
                self.log(f"[OK] Matched: '{race_name}' ({turn}) -> Year: {db_match['year']}, Grade: {db_match['grade']}")
            else:
                # Unmatched fallback: reconstruct with mapped year
                unmatched_count += 1
                self.log(f"[WARNING] Unmatched: '{race_name}' ({turn}, raw year: '{raw_year}'). Using fallback details.")
                converted_races.append({
                    "raceName": race_name,
                    "grade": moe_race.get("grade", "G3"),
                    "year": mapped_year,
                    "turn": turn,
                    "type": moe_race.get("type", "Turf"),
                    "location": moe_race.get("location", "Unknown"),
                    "length": moe_race.get("length", "Medium"),
                    "lengthM": moe_race.get("lengthM", "2000 m")
                })
                
        # Save output file
        final_output_path = os.path.join(output_dir, output_filename)
        try:
            with open(final_output_path, "w", encoding="utf-8") as f:
                json.dump(converted_races, f, ensure_ascii=False, indent=2)
            self.log("-" * 50)
            self.log(f"SUCCESS: Saved converted file to {final_output_path}")
            self.log(f"Matched races: {matched_count} | Fallbacks used: {unmatched_count}")
            
            # Show popup summary
            summary_msg = f"Successfully converted {len(converted_races)} races!\n\n"
            summary_msg += f"Matched with database: {matched_count}\n"
            summary_msg += f"Warnings (unmatched fallbacks): {unmatched_count}\n\n"
            summary_msg += f"File saved to:\n{final_output_path}"
            
            if unmatched_count > 0:
                messagebox.showwarning("Conversion Finished (with Warnings)", summary_msg)
            else:
                messagebox.showinfo("Conversion Success", summary_msg)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save output file:\n{e}")
            self.log(f"FAILED: IO error writing to {final_output_path}")

if __name__ == "__main__":
    app = ConverterApp()
    app.mainloop()
