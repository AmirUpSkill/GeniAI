from app.core.security import generate_session_token, hash_session_token


def test_generate_session_token_returns_opaque_random_token() -> None:
    token_one = generate_session_token()
    token_two = generate_session_token()

    assert token_one != token_two
    assert len(token_one) >= 32


def test_hash_session_token_is_stable_and_hides_raw_token() -> None:
    token = "raw-session-token"

    hashed_once = hash_session_token(token, "secret-key")
    hashed_twice = hash_session_token(token, "secret-key")

    assert hashed_once == hashed_twice
    assert hashed_once != token
    assert len(hashed_once) == 64


def test_hash_session_token_depends_on_secret_key() -> None:
    token = "raw-session-token"

    assert hash_session_token(token, "secret-one") != hash_session_token(token, "secret-two")
