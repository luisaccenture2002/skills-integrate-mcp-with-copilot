import argparse
from getpass import getpass

from src.auth import set_teacher_password


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create or update a teacher account for the activities app."
    )
    parser.add_argument("username", help="Teacher username or email address")
    args = parser.parse_args()

    password = getpass("Password (at least 12 characters): ")
    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        parser.error("Passwords do not match.")

    try:
        set_teacher_password(args.username, password)
    except ValueError as error:
        parser.error(str(error))

    print(f"Teacher account saved for {args.username.strip().lower()}.")


if __name__ == "__main__":
    main()
