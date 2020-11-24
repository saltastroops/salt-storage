"""Authentication and authorization."""
import os
from typing import Any, Optional

import httpx
import jwt


def parse_token(token: str, refetch_public_key_on_failure: bool = False) -> Any:
    """
    Parse a JWT token.

    If parsing fails for reasons other than an expred token and if in addition the
    refetch_public_key_on_failure argument is True, the public key for validating
    is re-requested from the SALT API server and another attempt at parsing the token is
    made.
    """
    try:
        public_key = get_public_key()
        return jwt.decode(token, public_key, algorithms=["RS256"])
    except jwt.ExpiredSignatureError:
        raise ValueError("The token has expired.")
    except Exception:
        if refetch_public_key_on_failure:
            update_public_key()
            return parse_token(token, refetch_public_key_on_failure=False)
        else:
            raise ValueError("Invalid token.")


def get_public_key() -> str:
    """
    Get the public key for validating SALT API server tokens.

    The public key is read from file. If that fails, the token is requested from the
    salt api server, stored amd returned.
    """
    public_key = read_public_key()
    if public_key:
        return public_key

    return update_public_key()


def update_public_key() -> str:
    """
    Update the public key for validating SALT API server tokens.

    The public key is requested from the SALT API server, stored and returned.
    """
    public_key = request_public_key()
    store_public_key(public_key)
    return public_key


def request_public_key() -> str:
    """Request the public key for token authentication from the SALT API server."""
    response = httpx.get(f"{os.environ['SALT_API_URL']}/public-key")
    print(f"{os.environ['SALT_API_URL']}/public-key", response)
    if response.status_code != 200:
        raise Exception(
            "The public key could not be requested from the SALT API server."
        )
    return response.text


def read_public_key() -> Optional[str]:
    """
    Read the public key from file.

    The key must have been stored by means of the store_public_key function. None is
    returned if there is an exception.
    """
    try:
        with open(os.environ["SALT_API_PUBLIC_KEY_FILE"]) as f:
            return f.read()
    except Exception:
        return None


def store_public_key(public_key: str) -> None:
    """
    Store the given public key on disk.

    The stored key can be read with the read_public_key function.
    """
    with open(os.environ["SALT_API_PUBLIC_KEY_FILE"], "w") as f:
        f.write(public_key)
