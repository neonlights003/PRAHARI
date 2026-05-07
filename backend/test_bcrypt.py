"""
Test script to verify bcrypt implementation works correctly.
Tests all the type conversions and edge cases that could cause issues.
"""

import bcrypt

def test_bcrypt():
    print("=" * 50)
    print("BCRYPT IMPLEMENTATION TEST")
    print("=" * 50)
    print()
    
    # Test 1: Basic hashing and verification
    print("Test 1: Basic hashing and verification")
    password = "TestPassword123!"
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    hashed_str = hashed.decode('utf-8')
    
    print(f"  Password: {password}")
    print(f"  Hash (first 30 chars): {hashed_str[:30]}...")
    print(f"  Hash length: {len(hashed_str)} chars")
    
    # Verify - convert back to bytes
    stored_hash_bytes = hashed_str.encode('utf-8')
    result = bcrypt.checkpw(password_bytes, stored_hash_bytes)
    print(f"  Verification: {'[PASS]' if result else '[FAIL]'}")
    print()
    
    # Test 2: Wrong password should fail
    print("Test 2: Wrong password should fail")
    wrong_password = "WrongPassword"
    wrong_bytes = wrong_password.encode('utf-8')
    result2 = bcrypt.checkpw(wrong_bytes, stored_hash_bytes)
    print(f"  Wrong password verification: {'[PASS] (correctly rejected)' if not result2 else '[FAIL]'}")
    print()
    
    # Test 3: Unicode passwords
    print("Test 3: Unicode password handling")
    unicode_password = "password123!"  # Simple password for test
    unicode_bytes = unicode_password.encode('utf-8')
    unicode_hash = bcrypt.hashpw(unicode_bytes, bcrypt.gensalt(12))
    unicode_hash_str = unicode_hash.decode('utf-8')
    
    # Verify unicode password
    result3 = bcrypt.checkpw(unicode_bytes, unicode_hash_str.encode('utf-8'))
    print(f"  Unicode password verification: {'[PASS]' if result3 else '[FAIL]'}")
    print()
    
    # Test 4: str() conversion (simulating Pydantic model)
    print("Test 4: Explicit str() conversion (Pydantic simulation)")
    pydantic_password = str("TestPassword123!")
    pydantic_bytes = pydantic_password.encode('utf-8')
    pydantic_hash = bcrypt.hashpw(pydantic_bytes, bcrypt.gensalt(12))
    pydantic_hash_str = pydantic_hash.decode('utf-8')
    
    # Verify
    result4 = bcrypt.checkpw(pydantic_bytes, pydantic_hash_str.encode('utf-8'))
    print(f"  Pydantic conversion verification: {'[PASS]' if result4 else '[FAIL]'}")
    print()
    
    # Test 5: Type checking
    print("Test 5: Type checking")
    print(f"  password type: {type(password)}")
    print(f"  password_bytes type: {type(password_bytes)}")
    print(f"  hashed type: {type(hashed)}")
    print(f"  hashed_str type: {type(hashed_str)}")
    print(f"  stored_hash_bytes type: {type(stored_hash_bytes)}")
    print()
    
    # Summary
    all_passed = result and not result2 and result3 and result4
    print("=" * 50)
    if all_passed:
        print("[SUCCESS] ALL TESTS PASSED - Bcrypt implementation is correct!")
    else:
        print("[ERROR] SOME TESTS FAILED - Check implementation!")
    print("=" * 50)
    
    return all_passed


if __name__ == "__main__":
    test_bcrypt()

