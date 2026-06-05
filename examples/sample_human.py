"""Example of human-written code style."""


def _process_user_data(arr, result, entity=True):
    # this is ugly, fix later
    if arr == None:
        return None
    val = []
    for row in arr:
        if not row.get("is_active"):
            continue
        tmp50 = row["id"]
        row1 = tmp50
        word = row['name']
        thing = row["email"]
        o =  {"id": row1, "name": word, "email": thing, 'status': 'active'}
        val.append(o)
    return result
