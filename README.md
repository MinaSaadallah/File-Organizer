# Advanced File Organizer

An intelligent, feature-rich file organization tool with GUI and command-line interfaces.

## Features

- **User-friendly GUI**: Intuitive interface with progress tracking and detailed statistics
- **Smart file categorization**: Automatically sorts files into appropriate folders based on file types
- **Customizable categories**: Add, edit, or remove file categories and their associated extensions
- **Date-based organization**: Option to create date subfolders within each category
- **Copy or move**: Choose whether to move files or just copy them
- **Undo functionality**: Easily revert the last organization operation
- **Exclude patterns**: Skip files matching specific patterns using regular expressions
- **Detailed statistics**: Get comprehensive information about organized files
- **Error handling**: Robust handling of permission issues and file conflicts
- **Logging**: Complete activity logging for troubleshooting
- **CLI support**: Run the organizer from command line for automation

## How to Use

### GUI Mode

1. Launch the application:

   ```
   python "File Organizer.py"
   ```

2. Select the directory you want to organize using the "Browse..." button

3. Choose your organization options:

   - Check "Organize by date" to create date-based subfolders
   - Check "Copy files instead of moving" to preserve original files

4. Click "Organize Files" to start the process

5. View the results in the progress section

### Command Line Mode

You can also run the application from the command line:

```
python "File Organizer.py" --cli <directory> [--date] [--copy]
```

Arguments:

- `--cli`: Run in command line mode
- `<directory>`: The directory to organize
- `--date`: (Optional) Organize files by date
- `--copy`: (Optional) Copy files instead of moving them

## Customization

### File Categories

The application comes with default file categories:

- Videos: .mp4, .mkv, .flv, .avi, .mov, etc.
- Photos: .jpg, .jpeg, .png, .gif, .bmp, etc.
- Music: .mp3, .wav, .aac, .flac, .ogg, etc.
- Documents: .pdf, .doc, .docx, .xls, .xlsx, etc.
- Archives: .zip, .rar, .7z, .tar, .gz, etc.
- Code: .py, .java, .cpp, .js, .html, etc.
- Executables: .exe, .msi, .app, .bat, .sh

You can add, edit, or remove categories in the "Settings" tab.

### Exclude Patterns

Use regular expressions to define patterns for files you want to exclude from organization.
For example:

- `^temp.*` - Excludes files starting with "temp"
- `.*\.tmp$` - Excludes files ending with .tmp
- `^backup_` - Excludes files starting with "backup\_"

## Requirements

- Python 3.6 or higher
- Tkinter (usually included with Python)

## License

This project is open-source software.
