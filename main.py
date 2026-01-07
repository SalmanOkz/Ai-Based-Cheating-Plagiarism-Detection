"""
Main Application - FIXED
"""
import cv2
import argparse
import time
from pathlib import Path

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Vision Guardian Proctoring System')
    parser.add_argument('--source', type=str, default='0',
                       help='Video source (0 for webcam, path for video file)')
    parser.add_argument('--output', type=str, default='proctoring_results',
                       help='Output directory')
    parser.add_argument('--max-frames', type=int, default=None,
                       help='Maximum frames to process')
    parser.add_argument('--no-gaze', action='store_true',
                       help='Disable gaze tracking')
    parser.add_argument('--no-objects', action='store_true',
                       help='Disable object detection')
    parser.add_argument('--show-fps', action='store_true',
                       help='Show FPS counter')
    parser.add_argument('--show-stats', action='store_true',
                       help='Show statistics overlay')
    parser.add_argument('--resolution', type=str, default='640x480',
                       help='Resolution (WxH)')
    
    return parser.parse_args()

def main():
    """Main application"""
    args = parse_arguments()
    
    # Parse resolution
    try:
        width, height = map(int, args.resolution.split('x'))
    except:
        width, height = 640, 480
    
    # Configuration
    config = {
        'output_dir': args.output,
        'enable_gaze': not args.no_gaze,
        'enable_objects': not args.no_objects,
        'save_output': True
    }
    
    # Import VisionGuardian
    try:
        from src.integrator import VisionGuardian
    except ImportError as e:
        print(f"❌ Failed to import VisionGuardian: {e}")
        return
    
    print("🚀 Initializing Vision Guardian...")
    guardian = VisionGuardian(config)
    
    # Check source
    if args.source == '0':
        source = 0
        source_type = 'Webcam'
    elif Path(args.source).exists():
        source = args.source
        source_type = 'Video File'
    else:
        print(f"❌ Source not found: {args.source}")
        return
    
    print(f"📹 Source: {source_type} ({args.source})")
    print(f"📐 Resolution: {width}x{height}")
    
    # Open video source
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"❌ Failed to open source: {args.source}")
        return
    
    # Set resolution for webcam
    if source == 0:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    print("\n🎬 Starting proctoring session...")
    print("=" * 50)
    print("Controls:")
    print("  Q - Quit")
    print("  S - Save screenshot")
    print("  P - Pause/Resume")
    print("  D - Toggle dashboard")
    print("  F - Toggle FPS display")
    print("  R - Reset statistics")
    print("=" * 50)
    
    # State variables
    paused = False
    show_dashboard = True
    show_fps = args.show_fps
    show_stats = args.show_stats
    
    frame_count = 0
    start_time = time.time()
    
    while True:
        if not paused:
            # Read frame
            ret, frame = cap.read()
            if not ret:
                print("⚠️ End of video stream")
                break
            
            # Resize frame
            if source != 0:  # Only resize if not webcam
                frame = cv2.resize(frame, (width, height))
            
            # Process frame
            result = guardian.process_frame(frame, frame_count)
            frame_count += 1
            
            # Calculate FPS
            elapsed = time.time() - start_time
            fps = frame_count / elapsed if elapsed > 0 else 0
            
            # Create display
            if show_dashboard:
                display_frame = guardian.annotate_frame(frame, result)
            else:
                display_frame = frame
            
            # Add overlays
            if show_fps:
                cv2.putText(display_frame, f"FPS: {fps:.1f}", 
                           (width - 100, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            if show_stats and frame_count % 30 == 0:
                stats = guardian.get_stats()
                cv2.putText(display_frame, f"Frames: {stats['frames_processed']}", 
                           (10, height - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(display_frame, f"Violations: {stats['violations_detected']}", 
                           (10, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Display
            cv2.imshow('Vision Guardian Proctoring', display_frame)
            
            # Print stats occasionally
            if frame_count % 100 == 0:
                stats = guardian.get_stats()
                print(f"📊 Frame {frame_count:06d} | "
                      f"FPS: {stats['fps']:.1f} | "
                      f"Violations: {stats['violations_detected']} | "
                      f"Alert: {result.get('alert_level', 'N/A')}")
        
        # Handle keyboard input
        key = cv2.waitKey(1 if not paused else 0) & 0xFF
        
        if key == ord('q'):
            print("\n🛑 Stopping proctoring session...")
            break
        elif key == ord('p'):
            paused = not paused
            status = "Paused" if paused else "Resumed"
            print(f"⏸️  {status}")
        elif key == ord('s'):
            # Save screenshot
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_path = Path(config['output_dir']) / f"screenshot_{timestamp}.jpg"
            cv2.imwrite(str(screenshot_path), display_frame)
            print(f"📸 Screenshot saved: {screenshot_path}")
        elif key == ord('d'):
            show_dashboard = not show_dashboard
            status = "enabled" if show_dashboard else "disabled"
            print(f"📊 Dashboard {status}")
        elif key == ord('f'):
            show_fps = not show_fps
            status = "enabled" if show_fps else "disabled"
            print(f"🎞️  FPS display {status}")
        elif key == ord('r'):
            # Reset statistics (you'll need to add this method to VisionGuardian)
            print("📊 Statistics reset")
        elif key == 27:  # ESC key
            print("\n🛑 ESC pressed, stopping...")
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    # Final summary
    print("\n" + "=" * 50)
    print("📊 SESSION SUMMARY")
    print("=" * 50)
    
    stats = guardian.get_stats()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for k, v in value.items():
                print(f"  {k}: {v}")
        else:
            print(f"{key}: {value}")
    
    print("=" * 50)


if __name__ == "__main__":
    main()