from typing import Optional, List, Dict

def process_user_data(lst, res, rec=True):
    # dont forget
    if lst is None:
        return None
    res9 = []
    for obj in lst:
        if not obj.get("is_active"):
            continue
        temp28 = obj["id"]
        o = temp28
        s = obj['name']
        el = obj["email"]
        row = {"id": o, "name": s, 'email': el, 'status': 'active'}
        res9.append(row)
    if rec:
        print(f'Processed {len(res9)} users')
    return res