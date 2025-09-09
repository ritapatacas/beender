import subprocess
import sys
import os
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import PathValidator


def get_settings():
    """Get current settings."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return {
        'faces_dir': os.path.join(script_dir, 'input', 'faces'),
        'footage_dir': os.path.join(script_dir, 'input', 'footage'),
        'output_dir': os.path.join(script_dir, 'output'),
        'skip_frames': 30,
        'tolerance': 0.5
    }


def customize_settings(settings):
    """Allow user to customize settings via select menu."""
    try:
        while True:
            choice = inquirer.select(
                message="Which setting would you like to change?",
                choices=[
                    Choice(f"Faces directory: {settings['faces_dir']}", "faces"),
                    Choice(f"Footage directory: {settings['footage_dir']}", "footage"),
                    Choice(f"Output directory: {settings['output_dir']}", "output"),
                    Choice(f"Skip frames: {settings['skip_frames']}", "skip"),
                    Choice(f"Match tolerance: {settings['tolerance']}", "tolerance"),
                    Choice("Done - proceed with these settings", "done")
                ]
            ).execute()
            
            if choice == "done":
                break
            elif choice == "faces":
                settings['faces_dir'] = inquirer.filepath(
                    message="Faces directory:",
                    default=settings['faces_dir'],
                    validate=PathValidator(is_dir=True, message="Please select a valid directory"),
                    only_directories=True
                ).execute()
            elif choice == "footage":
                settings['footage_dir'] = inquirer.filepath(
                    message="Footage directory:",
                    default=settings['footage_dir'],
                    validate=PathValidator(is_dir=True, message="Please select a valid directory"),
                    only_directories=True
                ).execute()
            elif choice == "output":
                settings['output_dir'] = inquirer.filepath(
                    message="Output directory:",
                    default=settings['output_dir'],
                    validate=PathValidator(is_dir=True, message="Please select a valid directory"),
                    only_directories=True
                ).execute()
            elif choice == "skip":
                settings['skip_frames'] = inquirer.number(
                    message="Frame skip (process every N frames for videos):",
                    default=settings['skip_frames'],
                    min_allowed=1,
                    max_allowed=1000
                ).execute()
            elif choice == "tolerance":
                settings['tolerance'] = inquirer.number(
                    message="Face recognition tolerance (0.1-1.0, lower = stricter):",
                    default=settings['tolerance'],
                    min_allowed=0.1,
                    max_allowed=1.0,
                    float_allowed=True
                ).execute()
        
        return settings
        
    except KeyboardInterrupt:
        print("\n\nCustomization cancelled by user.")
        return settings


def run_main_with_args(faces_dir, footage_dir, output_dir=None, skip=30, tolerance=0.5):
    """Run main.py with the specified arguments."""
    cmd = [
        sys.executable, 
        'main.py',
        '--faces', faces_dir,
        '--footage', footage_dir
    ]
    
    if output_dir:
        cmd.extend(['--output', output_dir])
    if skip != 30:
        cmd.extend(['--skip', str(skip)])
    if tolerance != 0.5:
        cmd.extend(['--tolerance', str(tolerance)])
    
    print(f"\n[INFO] Running: {' '.join(cmd)}")
    subprocess.run(cmd)


def main():
    """Main interactive menu."""
    try:
        print("\n")
        print("=" * 40)
        print("       TUMO Face Detection Tool")
        print("=" * 40)
        print("\n")
        
        settings = get_settings()
        
        print("Settings")
        print(f"Faces directory: {settings['faces_dir']}")
        print(f"Footage directory: {settings['footage_dir']}")
        print(f"Output directory: {settings['output_dir']}")
        print(f"Skip frames: {settings['skip_frames']}")
        print(f"Match tolerance: {settings['tolerance']}")
        print()
        
        proceed_with_defaults = inquirer.confirm(
            message="Do you want to proceed with default parameters?",
            default=True
        ).execute()
        
        if not proceed_with_defaults:
            settings = customize_settings(settings)
        
        confirm = inquirer.confirm(
            message=f"\nReady to process?\nFaces: {settings['faces_dir']}\nFootage: {settings['footage_dir']}\nOutput: {settings['output_dir']}\nSkip: {settings['skip_frames']}  |  Tolerance: {settings['tolerance']}",
            default=True
        ).execute()
        
        if confirm:
            run_main_with_args(
                settings['faces_dir'], 
                settings['footage_dir'], 
                settings['output_dir'], 
                settings['skip_frames'], 
                settings['tolerance']
            )
        else:
            print("Operation cancelled.")
            
    except KeyboardInterrupt:
        print("\n\nQuiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
