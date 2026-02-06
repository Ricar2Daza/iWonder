import bcrypt

def verify_password(plain_password, hashed_password):
    # bcrypt.checkpw requires bytes
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    
    return bcrypt.checkpw(plain_password, hashed_password)

def get_password_hash(password):
    if isinstance(password, str):
        password = password.encode('utf-8')
    # bcrypt.hashpw returns bytes, we decode to store as string
    return bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
