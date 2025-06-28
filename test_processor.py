#!/usr/bin/env python3
import os
import logging
from rehearsal_processor import RehearsalProcessor

def test_processor():
    """Test the rehearsal processor with existing songs folder"""
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    
    # Test with the existing songs folder as if it were rehearsal recordings
    processor = RehearsalProcessor(songs_folder="./songs")
    
    print("Testing Rehearsal Processor")
    print("===========================")
    print("Using ./songs folder as test input")
    print("This will analyze the reference songs to test the detection pipeline")
    
    # Process the songs folder as a test
    processor.process_folder("./songs", "./output/test")
    
    print("\nTest complete! Check ./output/test/rehearsal_analysis.csv")

if __name__ == "__main__":
    test_processor()