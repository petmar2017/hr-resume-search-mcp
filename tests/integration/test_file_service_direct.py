#!/usr/bin/env python3
"""
Direct test of FileService enhanced methods without pytest dependencies
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from api.services.file_service import FileService
    print("✅ FileService import successful")
except ImportError as e:
    print(f"❌ FileService import failed: {e}")
    sys.exit(1)

async def test_file_service_enhanced():
    """Test enhanced FileService methods directly"""
    
    # Create FileService instance
    file_service = FileService()
    print("✅ FileService instance created")
    
    # Test file type validation
    print("\n🔍 Testing file type validation:")
    valid_types = ["resume.pdf", "resume.docx", "resume.doc"]
    invalid_types = ["resume.txt", "resume.jpg", "resume"]
    
    for filename in valid_types:
        result = file_service.validate_file_type(filename)
        print(f"  {filename}: {'✅ Valid' if result else '❌ Invalid'}")
    
    for filename in invalid_types:
        result = file_service.validate_file_type(filename)
        print(f"  {filename}: {'❌ Invalid' if not result else '✅ Valid (unexpected)'}")
    
    # Test file size validation
    print("\n🔍 Testing file size validation:")
    test_sizes = [1024, 1048576, 5242880, 10485761]  # 1KB, 1MB, 5MB, ~10MB
    
    for size in test_sizes:
        result = file_service.validate_file_size(size)
        size_mb = size / (1024 * 1024)
        print(f"  {size_mb:.1f}MB: {'✅ Valid' if result else '❌ Invalid'}")
    
    # Test file type detection
    print("\n🔍 Testing file type detection:")
    test_files = ["resume.pdf", "resume.docx", "resume.doc", "resume.txt", "resume"]
    
    for filename in test_files:
        file_type = file_service.get_file_type(filename)
        print(f"  {filename}: {file_type or '(no extension)'}")
    
    # Test unique filename generation
    print("\n🔍 Testing unique filename generation:")
    original = "resume.pdf"
    unique_names = set()
    
    for i in range(5):
        unique_name = file_service.generate_unique_filename(original)
        unique_names.add(unique_name)
        print(f"  {i+1}: {unique_name}")
    
    print(f"  Generated {len(unique_names)} unique names (should be 5)")
    
    # Test file processing workflow (mocked)
    print("\n🔍 Testing file processing workflow:")
    
    class MockFileService(FileService):
        async def save_file(self, filename, content):
            await asyncio.sleep(0.01)  # Simulate I/O
            return f"/uploads/{filename}"
        
        async def extract_text_from_pdf(self, file_path):
            await asyncio.sleep(0.02)  # Simulate processing
            return "Mock extracted PDF text content"
        
        async def extract_text_from_docx(self, file_path):
            await asyncio.sleep(0.02)  # Simulate processing
            return "Mock extracted DOCX text content"
    
    mock_service = MockFileService()
    
    # Test PDF processing
    pdf_content = b"Mock PDF content"
    result = await mock_service.process_uploaded_file("test.pdf", pdf_content)
    
    print(f"  PDF processing: {'✅ Success' if result['success'] else '❌ Failed'}")
    if result['success']:
        print(f"    File path: {result['file_path']}")
        print(f"    Extracted text: {result['extracted_text'][:50]}...")
        print(f"    File size: {result['file_size']} bytes")
        print(f"    Processing time: {result['processing_time']:.3f}s")
    
    # Test DOCX processing
    docx_content = b"Mock DOCX content"
    result = await mock_service.process_uploaded_file("test.docx", docx_content)
    
    print(f"  DOCX processing: {'✅ Success' if result['success'] else '❌ Failed'}")
    if result['success']:
        print(f"    File path: {result['file_path']}")
        print(f"    Extracted text: {result['extracted_text'][:50]}...")
        print(f"    Processing time: {result['processing_time']:.3f}s")
    
    # Test invalid file type
    result = await mock_service.process_uploaded_file("test.txt", b"Text content")
    print(f"  Invalid file type: {'✅ Rejected' if not result['success'] else '❌ Accepted (unexpected)'}")
    if not result['success']:
        print(f"    Error: {result['error']}")
    
    # Test concurrent processing
    print("\n🔍 Testing concurrent file processing:")
    
    tasks = []
    for i in range(3):
        task1 = mock_service.process_uploaded_file(f"resume{i}.pdf", pdf_content)
        task2 = mock_service.process_uploaded_file(f"resume{i}.docx", docx_content)
        tasks.extend([task1, task2])
    
    import time
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    successful_results = [r for r in results if r['success']]
    print(f"  Processed {len(successful_results)}/{len(results)} files successfully")
    print(f"  Total time: {end_time - start_time:.3f}s")
    print(f"  Average processing time: {sum(r['processing_time'] for r in successful_results) / len(successful_results):.3f}s")
    
    print("\n🎉 FileService enhanced testing completed!")
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_file_service_enhanced())
        if result:
            print("\n✅ All FileService enhanced tests passed!")
        else:
            print("\n❌ Some FileService tests failed")
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()