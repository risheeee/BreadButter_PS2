import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_api_connection():
    """Test if API is running"""
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code == 200:
            print("API is running!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"API connection failed. Status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("Cannot connect to API. Make sure the backend is running on localhost:8000")
        return False

def test_profile_import():
    """Test profile import functionality"""
    print("\n Testing Profile Import...")
    
    # Test data
    test_profile = {
        "user_id": "test_photographer_001",
        "sources": [
            "https://instagram.com/amazing_photographer",
            "https://linkedin.com/in/john-photographer",
            "https://johnphotography.com"
        ],
        "source_types": ["instagram", "linkedin", "website"]
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/import-profile",
            json=test_profile,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("Profile import successful!")
            print(f"   User ID: {data['data']['user_id']}")
            print(f"   Name: {data['data'].get('name', 'N/A')}")
            print(f"   Skills: {data['data'].get('skills', [])[:3]}...")
            print(f"   Portfolio items: {len(data['data'].get('portfolio_items', []))}")
            return data['data']['user_id']
        else:
            print(f"Profile import failed. Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error during profile import: {e}")
        return None

def test_get_profile(user_id):
    """Test getting a specific profile"""
    print(f"\nTesting Get Profile for: {user_id}")
    
    try:
        response = requests.get(f"{API_BASE}/profile/{user_id}")
        
        if response.status_code == 200:
            data = response.json()
            profile = data['data']
            print("Profile retrieved successfully!")
            print(f"   Name: {profile.get('name', 'N/A')}")
            print(f"   Bio: {profile.get('bio', 'N/A')[:100]}...")
            print(f"   Profession: {profile.get('profession', 'N/A')}")
            print(f"   Skills: {len(profile.get('skills', []))} skills")
            print(f"   Social Links: {list(profile.get('social_links', {}).keys())}")
            print(f"   Portfolio: {len(profile.get('portfolio_items', []))} items")
            return True
        else:
            print(f"Get profile failed. Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error getting profile: {e}")
        return False

def test_list_profiles():
    """Test listing all profiles"""
    print("\nTesting List Profiles...")
    
    try:
        response = requests.get(f"{API_BASE}/profiles")
        
        if response.status_code == 200:
            data = response.json()
            profiles = data['data']
            print(f"Found {len(profiles)} profiles!")
            
            for i, profile in enumerate(profiles[:3], 1):  # Show first 3
                print(f"   {i}. {profile.get('name', profile['user_id'])}")
                print(f"      Profession: {profile.get('profession', 'N/A')}")
                print(f"      Skills: {profile.get('skills', [])[:3]}")
                print(f"      Created: {profile.get('created_at', 'N/A')}")
                
            if len(profiles) > 3:
                print(f"   ... and {len(profiles) - 3} more")
            return True
        else:
            print(f"List profiles failed. Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error listing profiles: {e}")
        return False

def test_multiple_profiles():
    """Test importing multiple different profiles"""
    print("\nTesting Multiple Profile Types...")
    
    test_profiles = [
        {
            "user_id": "designer_sarah_001",
            "sources": ["https://instagram.com/sarahdesigns", "https://sarahcreative.com"],
            "source_types": ["instagram", "website"]
        },
        {
            "user_id": "filmmaker_mike_002", 
            "sources": ["https://linkedin.com/in/mike-filmmaker", "https://mikefilms.com"],
            "source_types": ["linkedin", "website"]
        },
        {
            "user_id": "artist_emma_003",
            "sources": ["https://instagram.com/emma_art", "resume.pdf"],
            "source_types": ["instagram", "resume"]
        }
    ]
    
    successful_imports = 0
    
    for profile_data in test_profiles:
        print(f"\n   Importing: {profile_data['user_id']}")
        try:
            response = requests.post(
                f"{API_BASE}/import-profile",
                json=profile_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                successful_imports += 1
                print(f"    Success!")
            else:
                print(f"    Failed: {response.status_code}")
                
        except Exception as e:
            print(f"    Error: {e}")
        
        time.sleep(1)  # Brief pause between requests
    
    print(f"\n Results: {successful_imports}/{len(test_profiles)} profiles imported successfully")
    return successful_imports

def test_ai_features():
    """Test AI-specific features"""
    print("\nTesting AI Features...")
    
    # Test with a profile that should trigger AI analysis
    ai_test_profile = {
        "user_id": "ai_test_creator_001",
        "sources": [
            "https://instagram.com/creative_ai_test",
            "https://linkedin.com/in/ai-test-creative"
        ],
        "source_types": ["instagram", "linkedin"]
    }
    
    try:
        print("   Importing profile with AI analysis...")
        response = requests.post(
            f"{API_BASE}/import-profile",
            json=ai_test_profile,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            profile = data['data']
            
            print("    AI Analysis Results:")
            print(f"      Bio Generated: {'Yes' if profile.get('bio') else 'No'}")
            print(f"      Skills Extracted: {len(profile.get('skills', []))} skills")
            
            # Check portfolio AI analysis
            portfolio_with_ai = [
                item for item in profile.get('portfolio_items', [])
                if item.get('ai_analysis')
            ]
            print(f"      Portfolio AI Analysis: {len(portfolio_with_ai)} items analyzed")
            
            if portfolio_with_ai:
                sample_analysis = portfolio_with_ai[0].get('ai_analysis')
                if isinstance(sample_analysis, str):
                    try:
                        analysis_data = json.loads(sample_analysis)
                        print(f"      Sample Analysis: {analysis_data.get('content_type', 'N/A')}")
                    except:
                        print(f"      Sample Analysis: Available")
            
            return True
        else:
            print(f"    AI test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"    AI test error: {e}")
        return False

def run_comprehensive_test():
    """Run all tests in sequence"""
    print(" Smart Talent Profile Builder - API Test Suite")
    print("=" * 55)
    
    # Test results tracking
    tests_passed = 0
    total_tests = 6
    
    # 1. Test API connection
    if test_api_connection():
        tests_passed += 1
    
    # 2. Test profile import
    user_id = test_profile_import()
    if user_id:
        tests_passed += 1
        
        # 3. Test get profile (depends on import success)
        if test_get_profile(user_id):
            tests_passed += 1
    else:
        print(" Skipping get profile test (import failed)")
    
    # 4. Test list profiles
    if test_list_profiles():
        tests_passed += 1
    
    # 5. Test multiple profiles
    successful_imports = test_multiple_profiles()
    if successful_imports > 0:
        tests_passed += 1
    
    # 6. Test AI features
    if test_ai_features():
        tests_passed += 1
    
    # Final results
    print("\n" + "=" * 55)
    print(" TEST RESULTS SUMMARY")
    print("=" * 55)
    print(f" Tests Passed: {tests_passed}/{total_tests}")
    print(f" Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print(" All tests passed! The API is working correctly.")
    elif tests_passed >= total_tests * 0.8:
        print("  Most tests passed. Some features may need attention.")
    else:
        print(" Several tests failed. Please check the API and configuration.")
    
    print("\n Next Steps:")
    print("   1. Check profiles in the frontend: http://localhost:3000")
    print("   2. View API docs: http://localhost:8000/docs")
    print("   3. Test with real social media URLs")
    print("   4. Configure Gemini AI key for full AI features")
    
    return tests_passed == total_tests

def test_error_handling():
    """Test API error handling"""
    print("\n Testing Error Handling...")
    
    # Test invalid profile import
    invalid_profile = {
        "user_id": "",  # Empty user ID
        "sources": [],  # Empty sources
        "source_types": []
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/import-profile",
            json=invalid_profile,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print("    Invalid input properly rejected")
        else:
            print("    Invalid input was accepted (should be rejected)")
            
    except Exception as e:
        print(f"   Error handling working: {e}")
    
    # Test non-existent profile
    try:
        response = requests.get(f"{API_BASE}/profile/non_existent_user")
        if response.status_code == 404:
            print("    Non-existent profile properly returns 404")
        else:
            print(f"    Expected 404, got {response.status_code}")
    except Exception as e:
        print(f"    Error testing non-existent profile: {e}")

if __name__ == "__main__":
    # Add error handling test
    print(" Smart Talent Profile Builder - Comprehensive API Test")
    print("=" * 60)
    
    success = run_comprehensive_test()
    
    # Additional error handling tests
    test_error_handling()
    
    print("\n Testing Complete!")
    if success:
        print(" Ready for demo!")
    else:
        print("Some issues found - check logs above.")