#!/usr/bin/env python3
"""
Simple test script to verify both frontend and backend are working
"""

import requests
import time
import sys


def test_backend():
    """Test the FastAPI backend"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and healthy!")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Backend returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        return False


def test_frontend():
    """Test the Next.js frontend"""
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running!")
            print(f"   Status code: {response.status_code}")
            return True
        else:
            print(f"❌ Frontend returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Frontend is not running on http://localhost:3000")
        return False
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Testing Multi-Persona Feedback System Setup...")
    print("=" * 50)

    # Test backend
    print("\n🔧 Testing Backend (FastAPI)...")
    backend_ok = test_backend()

    # Test frontend
    print("\n🎨 Testing Frontend (Next.js)...")
    frontend_ok = test_frontend()

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Backend:  {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"   Frontend: {'✅ PASS' if frontend_ok else '❌ FAIL'}")

    if backend_ok and frontend_ok:
        print("\n🎉 All tests passed! Your development environment is ready.")
        print("   - Frontend: http://localhost:3000")
        print("   - Backend:  http://localhost:8000")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the services.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
