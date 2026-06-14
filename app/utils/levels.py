def get_student_level(coins: int):

    levels = [
        {
            "name": "Bronze",
            "min": 0,
            "image": "/media/levels/bronze.png",
            "next_level": "Silver",
            "next_level_coins": 500
        },
        {
            "name": "Silver",
            "min": 500,
            "image": "/media/levels/silver.png",
            "next_level": "Gold",
            "next_level_coins": 1500
        },
        {
            "name": "Gold",
            "min": 1500,
            "image": "/media/levels/gold.png",
            "next_level": "Diamond",
            "next_level_coins": 5000
        },
        {
            "name": "Diamond",
            "min": 5000,
            "image": "/media/levels/diamond.png",
            "next_level": "Legend",
            "next_level_coins": 10000
        },
        {
            "name": "Legend",
            "min": 10000,
            "image": "/media/levels/legend.png",
            "next_level": None,
            "next_level_coins": None
        }
    ]

    current = levels[0]

    for level in levels:
        if coins >= level["min"]:
            current = level

    # 🔥 progress
    current_min = current["min"]
    next_min = current["next_level_coins"]

    if next_min:
        progress = (
            (coins - current_min) /
            (next_min - current_min)
        ) * 100
    else:
        progress = 100

    current["progress_percent"] = round(progress)

    return current