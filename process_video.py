import sys
import os
import cv2
import numpy as np

def is_blurry(frame, threshold=100):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var < threshold

def is_blackout(frame, threshold=30):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_intensity = np.mean(gray)
    return mean_intensity < threshold

def contains_steel_part(frame):
    # Simple heuristic: steel parts are bright and reflective, often grayish/white.
    # We'll check if there are enough pixels with high brightness and low saturation.
    
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    brightness = hsv[:, :, 2]  # Value channel
    saturation = hsv[:, :, 1]  # Saturation channel
    
    # Steel typically bright (value > 200), low saturation (< 50)
    steel_mask = (brightness > 200) & (saturation < 50)
    steel_pixels = np.sum(steel_mask)
    total_pixels = frame.shape[0] * frame.shape[1]
    
    # If > 1% pixels are steel-like, consider steel part present
    return steel_pixels > (0.01 * total_pixels)

def process_video(input_path, output_path, chunk_duration_sec=10, blur_threshold=100, blackout_threshold=30):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print("❌ Could not open input video.")
        return False
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    chunk_frames = int(fps * chunk_duration_sec)
    frame_buffer = []
    good_chunks = []
    
    current_frame = 0
    
    print(f"Video opened: {input_path}")
    print(f"Resolution: {width}x{height}, FPS: {fps}, Total frames: {total_frames}")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            # End of video - process remaining buffered frames if any
            if frame_buffer:
                good_chunks.append(frame_buffer)
            break
        
        frame_buffer.append(frame)
        current_frame += 1
        
        # If we collected enough frames for a chunk or it's the last frames
        if len(frame_buffer) == chunk_frames or current_frame == total_frames:
            # Analyze chunk
            keep_chunk = False
            
            # Check for steel parts in chunk
            for f in frame_buffer:
                if contains_steel_part(f):
                    keep_chunk = True
                    break
            
            # Check for blurry or blackout frames; if too many bad frames, discard chunk
            bad_frames = 0
            for f in frame_buffer:
                if is_blurry(f, blur_threshold) or is_blackout(f, blackout_threshold):
                    bad_frames += 1
            # If more than 50% frames are bad, discard chunk
            if bad_frames > len(frame_buffer) * 0.5:
                keep_chunk = False
            
            if keep_chunk:
                good_chunks.append(frame_buffer)
                print(f"Chunk {len(good_chunks)} kept with {len(frame_buffer)} frames.")
            else:
                print(f"Chunk discarded due to low quality or no steel parts.")
            
            frame_buffer = []
    
    # Write all good chunks to output video
    total_written_frames = 0
    for chunk in good_chunks:
        for f in chunk:
            out.write(f)
            total_written_frames += 1
    
    cap.release()
    out.release()
    
    print(f"✅ Processing complete. Written frames: {total_written_frames}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python process_video.py <input_video> <output_video>")
        sys.exit(1)
    
    input_video = sys.argv[1]
    output_video = sys.argv[2]
    
    success = process_video(input_video, output_video)
    if not success:
        sys.exit(1)
