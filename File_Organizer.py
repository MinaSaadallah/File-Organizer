import os
import shutil
import logging
import datetime
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import re
from pathlib import Path
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='file_organizer.log',
    filemode='a'
)

class FileOrganizer:
    def __init__(self):
        # Default file types
        self.default_file_types = {
            'Videos': ['.mp4', '.mkv', '.flv', '.avi', '.mov', '.wmv', '.m4v', '.mpg', '.mpeg'],
            'Photos': ['.jpg', '.jpeg', '.png', '.cr2', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.raw'],
            'Music': ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a', '.wma', '.opus'],
            'Documents': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt', '.md', '.csv'],
            'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
            'Code': ['.py', '.java', '.cpp', '.c', '.h', '.js', '.html', '.css', '.php', '.rb', '.go', '.rs', '.json'],
            'Executables': ['.exe', '.msi', '.app', '.bat', '.sh']
        }
        
        # Load custom settings if available
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'organizer_config.json')
        self.file_types = self.load_config()
        
        # Operations history for undo functionality
        self.operation_history = []
        self.excluded_patterns = []
        
        # Statistics
        self.stats = {
            "total_files": 0,
            "organized_files": 0,
            "skipped_files": 0,
            "categories": {},
            "total_size": 0
        }

    def load_config(self):
        """Load configuration from file or return defaults"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    logging.info("Configuration loaded successfully")
                    
                    # Extract excluded patterns if available
                    if 'excluded_patterns' in config:
                        self.excluded_patterns = config['excluded_patterns']
                        
                    return config.get('file_types', self.default_file_types)
            return self.default_file_types
        except Exception as e:
            logging.error(f"Error loading configuration: {str(e)}")
            return self.default_file_types

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump({
                    'file_types': self.file_types,
                    'excluded_patterns': self.excluded_patterns
                }, f, indent=4)
            logging.info("Configuration saved successfully")
        except Exception as e:
            logging.error(f"Error saving configuration: {str(e)}")

    def is_excluded(self, filename):
        """Check if file should be excluded based on patterns"""
        for pattern in self.excluded_patterns:
            if re.search(pattern, filename):
                return True
        return False

    def organize_files(self, directory, organize_by_date=False, copy_instead_of_move=False):
        """Organize files in the specified directory"""
        try:
            # Reset statistics
            self.stats = {
                "total_files": 0,
                "organized_files": 0,
                "skipped_files": 0,
                "categories": {category: 0 for category in self.file_types.keys()},
                "categories": {category: 0 for category in self.file_types.keys() | {'Others'}},
                "total_size": 0
            }
            
            # Create a folder for each file type if it doesn't exist
            for folder in self.file_types.keys():
                folder_path = os.path.join(directory, folder)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
            
            # Create the "Others" folder if it doesn't exist
            others_folder = os.path.join(directory, "Others")
            if not os.path.exists(others_folder):
                os.makedirs(others_folder)
            
            # Iterate over the files in the directory
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                
                # Skip directories and the script itself
                if os.path.isdir(file_path) or filename == os.path.basename(__file__) or filename.endswith('.log'):
                    continue
                
                # Skip excluded files
                if self.is_excluded(filename):
                    self.stats["skipped_files"] += 1
                    logging.info(f"Skipped file (excluded pattern): {filename}")
                    continue
                    
                self.stats["total_files"] += 1
                
                # Get file size
                file_size = os.path.getsize(file_path)
                self.stats["total_size"] += file_size
                
                # Determine the destination folder
                destination_folder = None
                for folder, extensions in self.file_types.items():
                    if any(filename.lower().endswith(ext) for ext in extensions):
                        destination_folder = folder
                        break
                
                # If no matching file type, move to Others
                if not destination_folder:
                    destination_folder = "Others"
                
                # Prepare destination path with optional date organization
                if organize_by_date:
                    # Get file creation/modification date
                    mod_time = os.path.getmtime(file_path)
                    date_str = datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d')
                    
                    # Create date subfolder if it doesn't exist
                    date_folder = os.path.join(directory, destination_folder, date_str)
                    if not os.path.exists(date_folder):
                        os.makedirs(date_folder)
                        
                    destination_path = os.path.join(date_folder, filename)
                else:
                    destination_path = os.path.join(directory, destination_folder, filename)
                
                # Handle file operation (copy or move)
                try:
                    # Save operation for undo functionality
                    operation = {
                        "operation": "copy" if copy_instead_of_move else "move",
                        "source": file_path,
                        "destination": destination_path
                    }
                    
                    # Handle potential file conflicts
                    if os.path.exists(destination_path):
                        base, extension = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(destination_path):
                            new_filename = f"{base}_{counter}{extension}"
                            if organize_by_date:
                                destination_path = os.path.join(directory, destination_folder, date_str, new_filename)
                            else:
                                destination_path = os.path.join(directory, destination_folder, new_filename)
                            counter += 1
                        
                        operation["destination"] = destination_path
                    
                    if copy_instead_of_move:
                        shutil.copy2(file_path, destination_path)
                        logging.info(f"Copied: {filename} -> {destination_path}")
                    else:
                        shutil.move(file_path, destination_path)
                        logging.info(f"Moved: {filename} -> {destination_path}")
                    
                    # Add to history for undo
                    self.operation_history.append(operation)
                    
                    # Update statistics
                    self.stats["organized_files"] += 1
                    self.stats["categories"][destination_folder] = self.stats["categories"].get(destination_folder, 0) + 1
                    
                except (PermissionError, OSError) as e:
                    self.stats["skipped_files"] += 1
                    logging.error(f"Error organizing {filename}: {str(e)}")
                
            return self.stats
            
        except Exception as e:
            logging.error(f"Error during organization: {str(e)}")
            raise
    
    def undo_last_operation(self):
        """Undo the last file operation"""
        if not self.operation_history:
            logging.warning("No operations to undo")
            return False
        
        operation = self.operation_history.pop()
        try:
            if operation["operation"] == "move":
                # For move, we move the file back to its original location
                if os.path.exists(operation["destination"]):
                    shutil.move(operation["destination"], operation["source"])
                    logging.info(f"Undone move: {operation['destination']} -> {operation['source']}")
                    return True
            elif operation["operation"] == "copy":
                # For copy, we just delete the copied file
                if os.path.exists(operation["destination"]):
                    os.remove(operation["destination"])
                    logging.info(f"Undone copy: Removed {operation['destination']}")
                    return True
            
            return False
        except Exception as e:
            logging.error(f"Error undoing operation: {str(e)}")
            return False

    def add_exclude_pattern(self, pattern):
        """Add a pattern to exclude from organization"""
        try:
            # Validate pattern
            re.compile(pattern)
            self.excluded_patterns.append(pattern)
            self.save_config()
            logging.info(f"Added exclude pattern: {pattern}")
            return True
        except re.error:
            logging.error(f"Invalid regex pattern: {pattern}")
            return False

    def get_summary(self):
        """Get a summary of the organization operation"""
        summary = f"Organization Summary:\n"
        summary += f"Total files processed: {self.stats['total_files']}\n"
        summary += f"Files organized: {self.stats['organized_files']}\n"
        summary += f"Files skipped: {self.stats['skipped_files']}\n"
        summary += f"Total size processed: {self.format_size(self.stats['total_size'])}\n\n"
        
        summary += "Files by category:\n"
        for category, count in self.stats['categories'].items():
            if count > 0:
                summary += f"  - {category}: {count}\n"
                
        return summary
    
    def format_size(self, size_bytes):
        """Format bytes into human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024 or unit == 'GB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024

class FileOrganizerCLI:
    def __init__(self):
        self.organizer = FileOrganizer()
        self.running = True
        
    def display_banner(self):
        """Display application banner"""
        print("\n" + "="*60)
        print("               ADVANCED FILE ORGANIZER")
        print("                    Terminal Edition")
        print("="*60)
        print("Type 'help' to see available commands\n")
    
    def display_help(self):
        """Display available commands"""
        print("\nAvailable commands:")
        print("  organize <directory>    - Organize files in specified directory")
        print("  settings                - Manage file type settings")
        print("  exclude                 - Manage exclude patterns")
        print("  undo                    - Undo last operation")
        print("  stats                   - Show last operation statistics")
        print("  help                    - Show this help message")
        print("  exit                    - Exit the application\n")
    
    def run(self):
        """Main CLI loop"""
        self.display_banner()
        
        while self.running:
            try:
                command = input("file-organizer> ").strip()
                
                if not command:
                    continue
                
                # Parse command and arguments
                parts = command.split(maxsplit=1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                # Process commands
                if cmd == "exit" or cmd == "quit":
                    self.running = False
                    
                elif cmd == "help":
                    self.display_help()
                    
                elif cmd == "organize":
                    self.handle_organize(args)
                    
                elif cmd == "settings":
                    self.manage_settings()
                    
                elif cmd == "exclude":
                    self.manage_exclude_patterns()
                    
                elif cmd == "undo":
                    self.handle_undo()
                    
                elif cmd == "stats":
                    print(self.organizer.get_summary())
                    
                else:
                    print(f"Unknown command: {cmd}")
                    print("Type 'help' to see available commands")
            
            except KeyboardInterrupt:
                print("\nType 'exit' to quit the application")
            except Exception as e:
                print(f"Error: {str(e)}")
    
    def handle_organize(self, args):
        """Handle organize command"""
        if not args:
            print("Usage: organize <directory>")
            return
            
        directory = args.strip()
        
        if not os.path.isdir(directory):
            print(f"Error: '{directory}' is not a valid directory")
            return
        
        # Get organization options
        organize_by_date = self.prompt_yes_no("Organize by date?", False)
        copy_instead_of_move = self.prompt_yes_no("Copy files instead of moving?", False)
        
        print(f"\nOrganizing files in: {directory}")
        print(f"  - {'Creating date-based folders' if organize_by_date else 'No date organization'}")
        print(f"  - {'Copying files' if copy_instead_of_move else 'Moving files'}")
        
        # Confirm before proceeding
        if not copy_instead_of_move:
            if not self.prompt_yes_no("This will move files in the selected directory. Continue?", False):
                return
        
        # Track start time for performance measurement
        start_time = time.time()
        
        try:
            # Show progress indicator
            print("Processing...", end="", flush=True)
            
            # Perform organization
            stats = self.organizer.organize_files(directory, organize_by_date, copy_instead_of_move)
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            
            # Clear progress indicator
            print("\r" + " " * 20 + "\r", end="")
            
            # Show results
            print("\n" + "="*50)
            print(self.organizer.get_summary())
            print(f"Operation completed in {elapsed_time:.2f} seconds")
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"\nError: {str(e)}")
    
    def handle_undo(self):
        """Handle undo command"""
        if self.organizer.undo_last_operation():
            print("Last operation has been undone.")
        else:
            print("No operations to undo or undo failed.")
    
    def manage_settings(self):
        """Manage file type settings"""
        while True:
            print("\nFile Type Settings:")
            print("  1. View current settings")
            print("  2. Add new category")
            print("  3. Edit category")
            print("  4. Delete category")
            print("  5. Save settings")
            print("  6. Return to main menu")
            
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                self.display_file_types()
            elif choice == "2":
                self.add_file_type_category()
            elif choice == "3":
                self.edit_file_type_category()
            elif choice == "4":
                self.delete_file_type_category()
            elif choice == "5":
                self.organizer.save_config()
                print("Settings saved successfully.")
            elif choice == "6":
                break
            else:
                print("Invalid choice. Please try again.")
    
    def display_file_types(self):
        """Display current file type settings"""
        print("\nCurrent File Type Categories:")
        
        for i, (category, extensions) in enumerate(self.organizer.file_types.items(), 1):
            print(f"{i}. {category}: {', '.join(extensions)}")
    
    def add_file_type_category(self):
        """Add a new file type category"""
        category = input("Enter new category name: ").strip()
        
        if not category:
            print("Category name cannot be empty.")
            return
            
        if category in self.organizer.file_types:
            print(f"Category '{category}' already exists.")
            return
            
        extensions_input = input("Enter file extensions (comma-separated): ").strip()
        
        if not extensions_input:
            print("Extensions cannot be empty.")
            return
            
        # Parse extensions
        extensions = [ext.strip() for ext in extensions_input.split(',')]
        # Ensure extensions start with a dot
        extensions = ['.' + ext.lstrip('.') for ext in extensions if ext]
        
        # Add to file types
        self.organizer.file_types[category] = extensions
        print(f"Category '{category}' added successfully.")
    
    def edit_file_type_category(self):
        """Edit an existing file type category"""
        self.display_file_types()
        
        categories = list(self.organizer.file_types.keys())
        category_index = input("\nEnter category number to edit: ").strip()
        
        try:
            index = int(category_index) - 1
            if 0 <= index < len(categories):
                category = categories[index]
                current_extensions = self.organizer.file_types[category]
                
                print(f"Editing category: {category}")
                print(f"Current extensions: {', '.join(current_extensions)}")
                
                extensions_input = input("Enter new file extensions (comma-separated): ").strip()
                
                if not extensions_input:
                    print("Extensions cannot be empty.")
                    return
                    
                # Parse extensions
                extensions = [ext.strip() for ext in extensions_input.split(',')]
                # Ensure extensions start with a dot
                extensions = ['.' + ext.lstrip('.') for ext in extensions if ext]
                
                # Update file types
                self.organizer.file_types[category] = extensions
                print(f"Category '{category}' updated successfully.")
            else:
                print("Invalid category number.")
        except ValueError:
            print("Please enter a valid number.")
    
    def delete_file_type_category(self):
        """Delete a file type category"""
        self.display_file_types()
        
        categories = list(self.organizer.file_types.keys())
        category_index = input("\nEnter category number to delete: ").strip()
        
        try:
            index = int(category_index) - 1
            if 0 <= index < len(categories):
                category = categories[index]
                
                if self.prompt_yes_no(f"Are you sure you want to delete the '{category}' category?", False):
                    del self.organizer.file_types[category]
                    print(f"Category '{category}' deleted successfully.")
            else:
                print("Invalid category number.")
        except ValueError:
            print("Please enter a valid number.")
    
    def manage_exclude_patterns(self):
        """Manage exclude patterns"""
        while True:
            print("\nExclude Patterns (Regex):")
            print("  1. View current patterns")
            print("  2. Add new pattern")
            print("  3. Delete pattern")
            print("  4. Return to main menu")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                self.display_exclude_patterns()
            elif choice == "2":
                self.add_exclude_pattern()
            elif choice == "3":
                self.delete_exclude_pattern()
            elif choice == "4":
                break
            else:
                print("Invalid choice. Please try again.")
    
    def display_exclude_patterns(self):
        """Display current exclude patterns"""
        print("\nCurrent Exclude Patterns:")
        
        if not self.organizer.excluded_patterns:
            print("  No patterns defined.")
            return
            
        for i, pattern in enumerate(self.organizer.excluded_patterns, 1):
            print(f"{i}. {pattern}")
    
    def add_exclude_pattern(self):
        """Add a new exclude pattern"""
        pattern = input("Enter regex pattern to exclude: ").strip()
        
        if not pattern:
            print("Pattern cannot be empty.")
            return
            
        if self.organizer.add_exclude_pattern(pattern):
            print(f"Pattern '{pattern}' added successfully.")
        else:
            print("Invalid regular expression pattern.")
    
    def delete_exclude_pattern(self):
        """Delete an exclude pattern"""
        self.display_exclude_patterns()
        
        if not self.organizer.excluded_patterns:
            return
            
        pattern_index = input("\nEnter pattern number to delete: ").strip()
        
        try:
            index = int(pattern_index) - 1
            if 0 <= index < len(self.organizer.excluded_patterns):
                pattern = self.organizer.excluded_patterns[index]
                
                if self.prompt_yes_no(f"Are you sure you want to delete the pattern '{pattern}'?", False):
                    self.organizer.excluded_patterns.pop(index)
                    self.organizer.save_config()
                    print(f"Pattern deleted successfully.")
            else:
                print("Invalid pattern number.")
        except ValueError:
            print("Please enter a valid number.")
    
    def prompt_yes_no(self, question, default=True):
        """Prompt for yes/no response"""
        default_str = "Y/n" if default else "y/N"
        response = input(f"{question} [{default_str}]: ").strip().lower()
        
        if not response:
            return default
            
        return response.startswith('y')

class FileOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced File Organizer")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.organizer = FileOrganizer()
        
        # Set app icon if available
        try:
            self.root.iconbitmap("folder_icon.ico")
        except:
            pass
        
        self.create_gui()
    
    def create_gui(self):
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook (tabbed interface)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        organize_tab = ttk.Frame(notebook)
        settings_tab = ttk.Frame(notebook)
        about_tab = ttk.Frame(notebook)
        
        notebook.add(organize_tab, text="Organize Files")
        notebook.add(settings_tab, text="Settings")
        notebook.add(about_tab, text="About")
        
        # --- Organize Files Tab ---
        self.create_organize_tab(organize_tab)
        
        # --- Settings Tab ---
        self.create_settings_tab(settings_tab)
        
        # --- About Tab ---
        self.create_about_tab(about_tab)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_organize_tab(self, parent):
        # Directory selection frame
        dir_frame = ttk.LabelFrame(parent, text="Directory Selection", padding=10)
        dir_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.dir_var = tk.StringVar()
        ttk.Label(dir_frame, text="Directory:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(dir_frame, textvariable=self.dir_var, width=50).grid(row=0, column=1, padx=5, sticky=tk.EW)
        ttk.Button(dir_frame, text="Browse...", command=self.browse_directory).grid(row=0, column=2, padx=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(parent, text="Organization Options", padding=10)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.date_organize_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Organize by date", variable=self.date_organize_var).grid(row=0, column=0, sticky=tk.W)
        
        self.copy_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Copy files instead of moving", variable=self.copy_var).grid(row=1, column=0, sticky=tk.W)
        
        # Action buttons frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Organize Files", command=self.start_organizing).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Undo Last Operation", command=self.undo_operation).pack(side=tk.LEFT, padx=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding=10)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        # Results text area
        self.results_text = tk.Text(progress_frame, wrap=tk.WORD, height=15)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.results_text, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)
    
    def create_settings_tab(self, parent):
        # File types frame
        file_types_frame = ttk.LabelFrame(parent, text="File Types", padding=10)
        file_types_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a scrollable frame for file types
        canvas = tk.Canvas(file_types_frame)
        scrollbar = ttk.Scrollbar(file_types_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # File type entries
        self.file_type_entries = {}
        row = 0
        
        for category, extensions in self.organizer.file_types.items():
            ttk.Label(scrollable_frame, text=f"{category}:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            
            # Create text entry for extensions
            ext_entry = tk.Text(scrollable_frame, height=2, width=40, wrap=tk.WORD)
            ext_entry.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=2)
            ext_entry.insert(tk.END, ", ".join(extensions))
            
            # Add buttons for managing this category
            btn_frame = ttk.Frame(scrollable_frame)
            btn_frame.grid(row=row, column=2, sticky=tk.EW, padx=5, pady=2)
            
            ttk.Button(btn_frame, text="Delete", command=lambda c=category: self.delete_category(c)).pack(side=tk.LEFT, padx=2)
            
            self.file_type_entries[category] = ext_entry
            row += 1
        
        # Add new category frame
        add_frame = ttk.Frame(scrollable_frame)
        add_frame.grid(row=row, column=0, columnspan=3, sticky=tk.EW, padx=5, pady=10)
        
        ttk.Label(add_frame, text="New Category:").pack(side=tk.LEFT, padx=5)
        self.new_category_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.new_category_var, width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(add_frame, text="Extensions:").pack(side=tk.LEFT, padx=5)
        self.new_extensions_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.new_extensions_var, width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(add_frame, text="Add Category", command=self.add_category).pack(side=tk.LEFT, padx=5)
        
        # Exclude patterns frame
        exclude_frame = ttk.LabelFrame(parent, text="Exclude Patterns (Regex)", padding=10)
        exclude_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Display current exclude patterns
        exclude_list_frame = ttk.Frame(exclude_frame)
        exclude_list_frame.pack(fill=tk.X, expand=True)
        
        ttk.Label(exclude_list_frame, text="Current exclude patterns:").pack(anchor=tk.W)
        
        # Exclude patterns list
        self.exclude_listbox = tk.Listbox(exclude_list_frame, height=5)
        self.exclude_listbox.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        for pattern in self.organizer.excluded_patterns:
            self.exclude_listbox.insert(tk.END, pattern)
        
        # Controls for exclude patterns
        exclude_controls_frame = ttk.Frame(exclude_frame)
        exclude_controls_frame.pack(fill=tk.X)
        
        self.exclude_pattern_var = tk.StringVar()
        ttk.Entry(exclude_controls_frame, textvariable=self.exclude_pattern_var, width=30).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(exclude_controls_frame, text="Add Pattern", command=self.add_exclude).pack(side=tk.LEFT, padx=5)
        ttk.Button(exclude_controls_frame, text="Remove Selected", command=self.remove_exclude).pack(side=tk.LEFT, padx=5)
        
        # Save settings button
        ttk.Button(parent, text="Save Settings", command=self.save_settings).pack(pady=10)
    
    def create_about_tab(self, parent):
        ttk.Label(parent, text="Advanced File Organizer", font=("Helvetica", 16, "bold")).pack(pady=20)
        ttk.Label(parent, text="Version 2.0").pack()
        ttk.Label(parent, text="© 2025").pack(pady=10)
        
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=20)
        
        info_text = (
            "This application helps you organize your files automatically based on their types.\n\n"
            "Features:\n"
            "• Organize files by type\n"
            "• Optional date-based organization\n"
            "• Copy instead of move option\n"
            "• Customizable file categories\n"
            "• Exclude patterns\n"
            "• Undo functionality\n"
            "• Detailed statistics\n\n"
            "For more information, see the README.md file."
        )
        
        info_label = ttk.Label(parent, text=info_text, wraplength=500, justify=tk.LEFT)
        info_label.pack(padx=20, pady=10, anchor=tk.W)
    
    def browse_directory(self):
        """Open directory browser dialog"""
        directory = filedialog.askdirectory(title="Select Directory to Organize")
        if directory:
            self.dir_var.set(directory)
    
    def start_organizing(self):
        """Start the organization process in a separate thread"""
        directory = self.dir_var.get()
        if not directory or not os.path.isdir(directory):
            messagebox.showerror("Error", "Please select a valid directory")
            return
        
        # Confirm before proceeding
        if not self.copy_var.get():  # Only ask for confirmation if we're moving files
            if not messagebox.askyesno("Confirm", "This will move files in the selected directory. Continue?"):
                return
        
        # Clear results
        self.results_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        self.status_var.set("Organizing files...")
        
        # Start organization in a separate thread to keep GUI responsive
        threading.Thread(target=self.run_organization, args=(directory,), daemon=True).start()
    
    def run_organization(self, directory):
        """Run the organization process in a background thread"""
        try:
            # Get options
            organize_by_date = self.date_organize_var.get()
            copy_instead_of_move = self.copy_var.get()
            
            # Run organization
            stats = self.organizer.organize_files(directory, organize_by_date, copy_instead_of_move)
            
            # Update progress and show results
            self.root.after(0, self.update_progress, 100)
            self.root.after(0, self.show_results, self.organizer.get_summary())
            self.root.after(0, lambda: self.status_var.set("Organization complete"))
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.root.after(0, self.show_results, error_msg)
            self.root.after(0, lambda: self.status_var.set("Error occurred"))
    
    def update_progress(self, value):
        """Update progress bar value"""
        self.progress_var.set(value)
    
    def show_results(self, text):
        """Show results in the text area"""
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, text)
    
    def undo_operation(self):
        """Undo the last file operation"""
        if self.organizer.undo_last_operation():
            self.status_var.set("Last operation undone")
            self.show_results("Last operation has been undone.")
        else:
            messagebox.showinfo("Undo", "No operations to undo or undo failed")
    
    def delete_category(self, category):
        """Delete a category from file types"""
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete the '{category}' category?"):
            if category in self.organizer.file_types:
                del self.organizer.file_types[category]
                self.update_settings_tab()
    
    def add_category(self):
        """Add a new category of file types"""
        category = self.new_category_var.get().strip()
        extensions_text = self.new_extensions_var.get().strip()
        
        if not category:
            messagebox.showerror("Error", "Category name cannot be empty")
            return
        
        if not extensions_text:
            messagebox.showerror("Error", "Extensions cannot be empty")
            return
        
        # Parse extensions
        extensions = [ext.strip() for ext in extensions_text.split(',')]
        # Ensure extensions start with a dot
        extensions = ['.' + ext.lstrip('.') for ext in extensions if ext]
        
        # Add to file types
        self.organizer.file_types[category] = extensions
        
        # Clear inputs
        self.new_category_var.set("")
        self.new_extensions_var.set("")
        
        # Update the settings tab
        self.update_settings_tab()
    
    def add_exclude(self):
        """Add an exclude pattern"""
        pattern = self.exclude_pattern_var.get().strip()
        if not pattern:
            return
            
        if self.organizer.add_exclude_pattern(pattern):
            self.exclude_listbox.insert(tk.END, pattern)
            self.exclude_pattern_var.set("")
        else:
            messagebox.showerror("Error", "Invalid regular expression pattern")
    
    def remove_exclude(self):
        """Remove selected exclude pattern"""
        selection = self.exclude_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        pattern = self.exclude_listbox.get(index)
        
        # Remove from organizer's list
        if pattern in self.organizer.excluded_patterns:
            self.organizer.excluded_patterns.remove(pattern)
            self.exclude_listbox.delete(index)
    
    def update_settings_tab(self):
        """Recreate the settings tab to reflect changes"""
        notebook = self.root.nametowidget(self.root.winfo_children()[0].winfo_children()[0])
        settings_tab = notebook.nametowidget(notebook.tabs()[1])
        
        # Clear the tab
        for widget in settings_tab.winfo_children():
            widget.destroy()
        
        # Recreate settings tab
        self.create_settings_tab(settings_tab)
    
    def save_settings(self):
        """Save current settings"""
        # Update file types from entries
        for category, entry in self.file_type_entries.items():
            extensions_text = entry.get("1.0", tk.END).strip()
            extensions = [ext.strip() for ext in extensions_text.split(',')]
            # Ensure extensions start with a dot
            extensions = ['.' + ext.lstrip('.') for ext in extensions if ext]
            self.organizer.file_types[category] = extensions
        
        # Save to file
        self.organizer.save_config()
        self.status_var.set("Settings saved")
        messagebox.showinfo("Settings", "Settings have been saved successfully")


# Main entry point
if __name__ == "__main__":
    # Check if running in GUI mode or command line mode
    import sys
    import argparse
    
    # Create a command-line argument parser
    parser = argparse.ArgumentParser(description="File Organizer - A tool to organize files into categorized folders")
    
    # Command mode subparsers
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--gui", "-g", action="store_true", help="Run in graphical user interface mode")
    mode_group.add_argument("--cli", "-c", action="store_true", help="Run in basic command-line mode (non-interactive)")
    
    # Arguments for CLI mode
    parser.add_argument("directory", nargs="?", help="Directory to organize (required for basic CLI mode)")
    parser.add_argument("--date", "-d", action="store_true", help="Organize files into date-based subfolders")
    parser.add_argument("--copy", "-cp", action="store_true", help="Copy files instead of moving them")
    parser.add_argument("--verbose", "-v", action="store_true", help="Display detailed output")
    parser.add_argument("--exclude", "-e", action="append", help="Regex patterns to exclude files (can be used multiple times)")
    
    args = parser.parse_args()
    
    # Check which mode to run in
    if args.gui:
        # GUI mode
        try:
            root = tk.Tk()
            app = FileOrganizerGUI(root)
            root.mainloop()
        except Exception as e:
            print(f"Error starting GUI: {str(e)}")
            print("Try running in terminal mode with: python File_Organizer.py")
    elif args.cli:
        # Basic command-line mode (non-interactive)
        if not args.directory:
            parser.error("the directory argument is required for CLI mode")
            
        # Create and configure the organizer
        organizer = FileOrganizer()
        
        # Add exclude patterns if provided
        if args.exclude:
            for pattern in args.exclude:
                if organizer.add_exclude_pattern(pattern):
                    print(f"Excluding files matching: {pattern}")
        
        # Show processing message
        print(f"Organizing files in: {args.directory}")
        print("Configuration:")
        print(f"  - {'Creating date-based folders' if args.date else 'No date organization'}")
        print(f"  - {'Copying files' if args.copy else 'Moving files'}")
        
        # Track start time for performance measurement
        start_time = time.time()
        
        # Perform organization
        try:
            stats = organizer.organize_files(args.directory, args.date, args.copy)
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            
            # Show results
            print("\n" + "="*50)
            print(organizer.get_summary())
            print(f"Operation completed in {elapsed_time:.2f} seconds")
            print("="*50)
            
            # Show additional info if verbose
            if args.verbose:
                print("\nDetailed log available in: file_organizer.log")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
    else:
        # Interactive terminal mode (default)
        try:
            cli = FileOrganizerCLI()
            cli.run()
        except Exception as e:
            print(f"Error in terminal interface: {str(e)}")
            print("For basic command-line mode, try: python File_Organizer.py --cli <directory>")
            print("For GUI mode, try: python File_Organizer.py --gui")
