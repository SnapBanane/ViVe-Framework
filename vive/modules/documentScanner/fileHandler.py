import os
import time
import shutil
from pathlib import Path

class DocumentFileHandler:
    def __init__(self, inbox_dir="inbox", output_dir="inbox"):
        self.inbox_dir = inbox_dir
        self.output_dir = output_dir
        os.makedirs(inbox_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # Supported image formats
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    def get_inbox_files(self):
        """Get all supported image files from inbox"""
        inbox_path = Path(self.inbox_dir)
        image_files = []
        
        for file_path in inbox_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                image_files.append(str(file_path))
        
        return sorted(image_files)
    
    def handle_processed_file(self, original_path, move_originals=False, delete_originals=False):
        """Handle the original file after processing"""
        if delete_originals:
            os.remove(original_path)
            return f"Deleted original: {os.path.basename(original_path)}"
        elif move_originals:
            processed_dir = os.path.join(self.inbox_dir, "processed")
            os.makedirs(processed_dir, exist_ok=True)
            dest_path = os.path.join(processed_dir, os.path.basename(original_path))
            shutil.move(original_path, dest_path)
            return f"Moved original to: processed/{os.path.basename(original_path)}"
        else:
            return f"Original kept: {os.path.basename(original_path)}"
    
    def generate_output_paths(self, image_path):
        """Generate output file paths for processed image and PDF"""
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        processed_img_path = os.path.join(self.output_dir, f"{base_name}_scanned.jpg")
        pdf_path = os.path.join(self.output_dir, f"{base_name}_scanned.pdf")
        
        return processed_img_path, pdf_path
    
    def auto_process_inbox(self, scanner, move_originals=False, delete_originals=False):
        """
        Auto-process all documents in inbox folder
        
        Args:
            scanner: DocumentScanner instance to use for processing
            move_originals: Move original files to processed subfolder
            delete_originals: Delete original files after processing
        
        Returns:
            Summary of processing results
        """
        image_files = self.get_inbox_files()
        
        if not image_files:
            return {
                "total_files": 0,
                "processed": 0,
                "failed": 0,
                "message": "No image files found in inbox"
            }
        
        results = []
        processed_count = 0
        failed_count = 0
        
        print(f"Processing {len(image_files)} files from inbox...")
        
        for image_path in image_files:
            print(f"Processing: {os.path.basename(image_path)}")
            
            result = scanner.process_document(image_path)
            results.append(result)
            
            if result["success"]:
                processed_count += 1
                
                # Handle original file
                handle_message = self.handle_processed_file(
                    image_path, move_originals, delete_originals
                )
                print(f"  ✓ {handle_message}")
                
                print(f"  ✓ Created: {os.path.basename(result['processed_image'])}")
                if result["pdf_path"]:
                    print(f"  ✓ Created: {os.path.basename(result['pdf_path'])}")
            else:
                failed_count += 1
                print(f"  ✗ Failed: {result['error']}")
        
        return {
            "total_files": len(image_files),
            "processed": processed_count,
            "failed": failed_count,
            "results": results,
            "message": f"Processed {processed_count}/{len(image_files)} files successfully"
        }
    
    def watch_inbox(self, scanner, interval=5, move_originals=True):
        """
        Continuously watch inbox for new files and process them
        
        Args:
            scanner: DocumentScanner instance to use for processing
            interval: Check interval in seconds
            move_originals: Move processed files to subfolder
        """
        print(f"Watching inbox folder: {self.inbox_dir}")
        print(f"Output folder: {self.output_dir}")
        print(f"Check interval: {interval} seconds")
        print("Press Ctrl+C to stop...")
        
        processed_files = set()
        
        try:
            while True:
                image_files = self.get_inbox_files()
                new_files = [f for f in image_files if f not in processed_files]
                
                if new_files:
                    print(f"\nFound {len(new_files)} new files:")
                    for file_path in new_files:
                        print(f"Processing: {os.path.basename(file_path)}")
                        result = scanner.process_document(file_path)
                        
                        if result["success"]:
                            print(f"  ✓ Success: {os.path.basename(result['processed_image'])}")
                            processed_files.add(file_path)
                            
                            if move_originals:
                                self.handle_processed_file(file_path, move_originals=True)
                        else:
                            print(f"  ✗ Failed: {result['error']}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nStopped watching inbox.")
    
    def cleanup_processed_folder(self, days_old=30):
        """Clean up old files in processed folder"""
        processed_dir = os.path.join(self.inbox_dir, "processed")
        if not os.path.exists(processed_dir):
            return {"cleaned": 0, "message": "Processed folder doesn't exist"}
        
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        cleaned_count = 0
        
        for file_path in Path(processed_dir).iterdir():
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                os.remove(file_path)
                cleaned_count += 1
        
        return {
            "cleaned": cleaned_count,
            "message": f"Cleaned {cleaned_count} files older than {days_old} days"
        }
    
    def get_file_stats(self):
        """Get statistics about files in directories"""
        stats = {
            "inbox_files": len(self.get_inbox_files()),
            "output_files": 0,
            "processed_files": 0
        }
        
        # Count output files
        if os.path.exists(self.output_dir):
            output_files = [f for f in os.listdir(self.output_dir) 
                          if os.path.isfile(os.path.join(self.output_dir, f))]
            stats["output_files"] = len(output_files)
        
        # Count processed files
        processed_dir = os.path.join(self.inbox_dir, "processed")
        if os.path.exists(processed_dir):
            processed_files = [f for f in os.listdir(processed_dir) 
                             if os.path.isfile(os.path.join(processed_dir, f))]
            stats["processed_files"] = len(processed_files)
        
        return stats