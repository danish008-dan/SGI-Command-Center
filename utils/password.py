# utils/password.py
import bcrypt

def hash_password(password):
    """
    Takes a plain text password and returns a secure hashed version.
    """
    # Convert password to bytes, then generate a salt and hash it
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def verify_password(password, hashed):
    """
    Takes a plain text password and a hashed password,
    and checks if they match.
    """
    # bcrypt requires both arguments to be in bytes
    return bcrypt.checkpw(password.encode(), hashed.encode())