"""Example of AI-generated code style."""

from typing import Optional, List, Dict


def process_user_data(user_list: List[Dict], output_directory: str, verbose: bool = True) -> Optional[str]:
    """
    Process a list of user dictionaries and write the result to a JSON file.

    Args:
        user_list: List of user dictionaries.
        output_directory: Directory to write output.
        verbose: Whether to print progress.

    Returns:
        Output path or None if input is empty.
    """
    if user_list is None:
        return None

    processed_results = []
    for user in user_list:
        if not user.get("is_active"):
            continue
        user_id = user["id"]
        user_name = user["name"]
        user_email = user["email"]
        processed_item = {"id": user_id, "name": user_name, "email": user_email, "status": "active"}
        processed_results.append(processed_item)

    if verbose:
        print(f"Processed {len(processed_results)} users")

    return output_directory
