import secrets
import string

def generate_temp_password(length=10):
    """
    Generates a secure random password.
    Ensures at least one uppercase, one lowercase, and one digit.
    """
    alphabet = string.ascii_letters + string.digits
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)):
            return password
