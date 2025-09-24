"""
a systematic way for me to create a training set on the outfits
cycle through each outfit, i enter in a score from 1 to 5
"""

import pandas as pd
import itertools
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

def rate_outfits(
    processed_dir=r"C:\Users\ciaod\OneDrive - Australian National University\Desktop\projects\threaded\data\wardrobe\bg_removed",
    output_file="data/training/outfit_ratings.csv"
):
    """cycle through outfit combos, show images, and rate them (1–5 stars style)"""

    # wardrobe pieces we’re working with
    shirts = [f"shirt_{i}_bg_removed.png" for i in range(1, 15)]
    pants = [f"pants_{i}_bg_removed.png" for i in range(1, 13)]
    shoes = [f"shoes_{i}_bg_removed.png" for i in range(1, 5)]

    # build every possible combo of shirt + pants + shoes
    combinations = list(itertools.product(shirts, pants, shoes))

    ratings = []

    print(f"total combinations: {len(combinations)}")

    # go through every combo in order
    for idx, (shirt, pant, shoe) in enumerate(combinations, start=1):
        print(f"\ncombo {idx}/{len(combinations)}: {shirt}, {pant}, {shoe}")

        # open a small figure with the three items side by side
        fig, axs = plt.subplots(3, 1, figsize=(4, 10))
        for ax, fname, title in zip(axs, [shirt, pant, shoe], ["Shirt", "Pants", "Shoes"]):
            path = os.path.join(processed_dir, fname)
            img = mpimg.imread(path)
            ax.imshow(img)
            ax.set_title(title)
            ax.axis("off")
        plt.tight_layout()
        plt.show()

        # ask for a 1–5 star style rating
        rating = input("rating (1–5 stars, leave blank to skip): ").strip()
        ratings.append(rating if rating else "")

    # when finished → save everything into a csv
    df = pd.DataFrame(combinations, columns=["shirt_id", "pants_id", "shoes_id"])
    df["rating"] = ratings

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False)

    return df


if __name__ == "__main__":
    rate_outfits()
