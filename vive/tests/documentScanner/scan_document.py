from vive.modules.documentScanner.scan import process_inbox, watch_inbox, get_stats

def main():
    print("=== Document Scanner ===")
    
    # Show current stats
    stats = get_stats()
    print(f"Files in inbox: {stats['inbox_files']}")
    
    if stats['inbox_files'] > 0:
        print("\nProcessing documents...")
        result = process_inbox(move_originals=True)
        
        print(f"\nResults:")
        print(f"  Total files: {result['total_files']}")
        print(f"  Successfully processed: {result['processed']}")
        print(f"  Failed: {result['failed']}")
        
        if result['failed'] > 0:
            print("\nErrors:")
            for r in result['results']:
                if not r['success']:
                    print(f"  {r['original_path']}: {r['error']}")
    
    # Optionally start watching for new files
    choice = input("\nWatch for new files? (y/n): ")
    if choice.lower() == 'y':
        print("Starting file watcher... Press Ctrl+C to stop")
        watch_inbox(interval=5)

if __name__ == "__main__":
    main()