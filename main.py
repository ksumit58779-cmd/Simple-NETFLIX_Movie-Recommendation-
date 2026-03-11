from tqdm import tqdm
import csv
import random
from fuzzywuzzy import process

print("📽️  Loading movies...")
movies = {}

with open('movies.csv', 'r', encoding='utf-8') as file:
    next(file)
    for line in file:
        parts = line.strip().split(',', 2)
        if len(parts) >= 2:
            movie_id = parts[0]
            title = parts[1]
            movies[movie_id] = title

print(f"✅ Loaded {len(movies)} movies!")

all_movie_titles = list(movies.values())

def find_movie(search_term, threshold=70):
    if search_term in all_movie_titles:
        return search_term
    matches = process.extract(search_term, all_movie_titles, limit=5)
    if matches and matches[0][1] >= threshold:
        print(f"  💡 Did you mean: {matches[0][0]} ? (confidence: {matches[0][1]}%)")
        confirm = input("  Use this? (y/n): ").strip().lower()
        if confirm == 'y':
            return matches[0][0]
    print(f"\n  ❌ '{search_term}' not found. Did you mean:")
    for i, (movie, score) in enumerate(matches[:5], 1):
        print(f"    {i}. {movie} ({score}% match)")
    choice = input("  Choose (1-5) or 'skip': ").strip()
    if choice.isdigit() and 1 <= int(choice) <= 5:
        return matches[int(choice)-1][0]
    return None

print("\n📊 Loading ratings (this takes ~90 seconds)...")
user_ratings = {}

print("📏 Counting lines...")
with open('ratings.csv', 'r', encoding='utf-8') as file:
    total_lines = sum(1 for line in file) - 1

print(f"📝 Found {total_lines:,} ratings to load!")

with open('ratings.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    next(reader)
    for row in tqdm(reader, total=total_lines, desc="Loading"):
        if len(row) >= 3:
            user_id = row[0]
            movie_id = row[1]
            try:
                rating = float(row[2])
            except ValueError:
                continue
            if movie_id in movies:
                title = movies[movie_id]
                if user_id not in user_ratings:
                    user_ratings[user_id] = {}
                user_ratings[user_id][title] = rating

print(f"\n✅ Loaded ratings from {len(user_ratings):,} users!")

print("\n⚡ Sampling users for faster processing...")
all_users = list(user_ratings.keys())
print(f"📊 Total users: {len(all_users):,}")

sample_size = 10000
if len(all_users) > sample_size:
    sampled_users = random.sample(all_users, sample_size)
    user_ratings = {user: user_ratings[user] for user in sampled_users}
    print(f"✅ Sampled {len(user_ratings):,} users (20x faster!)")
else:
    print(f"✅ Using all {len(all_users):,} users")

print("\n" + "="*60)
print("🎬 ENTER YOUR MOVIE RATINGS")
print("="*60)
print("You can rate:")
print("  1. One at a time (type movie name)")
print("  2. Multiple at once (format: Movie1:5, Movie2:4, Movie3:5)")
print("  3. Type 'done' when finished")

your_ratings = {}

while True:
    user_input = input("\n🎬 Enter movie(s): ").strip()
    if user_input.lower() == 'done':
        break
    if ',' in user_input:
        pairs = user_input.split(',')
        for pair in pairs:
            if ':' in pair:
                parts = pair.strip().rsplit(':', 1)
                if len(parts) == 2:
                    title = parts[0].strip()
                    matched_title = find_movie(title)
                    if matched_title:
                        title = matched_title
                    else:
                        continue
                    try:
                        rating = float(parts[1].strip())
                        if 1 <= rating <= 5:
                            your_ratings[title] = rating
                            print(f"  ✅ {title}: {rating} stars")
                        else:
                            print(f"  ❌ Invalid rating for {title} (must be 1-5)")
                    except ValueError:
                        print(f"  ❌ Invalid rating format for {title}")
            else:
                print(f"  ❌ Invalid format: {pair.strip()} (use Title:Rating)")
    else:
        if ':' in user_input:
            parts = user_input.rsplit(':', 1)
            if len(parts) == 2:
                title = parts[0].strip()
                matched_title = find_movie(title)
                if matched_title:
                    title = matched_title
                else:
                    continue
                try:
                    rating = float(parts[1].strip())
                    if 1 <= rating <= 5:
                        your_ratings[title] = rating
                        print(f"✅ Added: {title} → {rating} stars")
                    else:
                        print("❌ Rating must be 1-5")
                except ValueError:
                    print("❌ Invalid rating format")
        else:
            title = user_input
            matched_title = find_movie(title)
            if matched_title:
                title = matched_title
            else:
                continue
            rating_input = input(f"Rate '{title}' (1-5 stars): ").strip()
            try:
                rating = float(rating_input)
                if 1 <= rating <= 5:
                    your_ratings[title] = rating
                    print(f"✅ Added: {title} → {rating} stars")
                else:
                    print("❌ Rating must be 1-5")
            except ValueError:
                print("❌ Invalid rating")

if len(your_ratings) == 0:
    print("\n❌ No ratings provided! Please run again.")
    exit()

print("\n" + "="*60)
print("YOUR RATINGS:")
print("="*60)
for movie, rating in your_ratings.items():
    print(f"  {movie}: {'⭐' * int(rating)}")

print("\n" + "="*60)
print("🔍 FINDING USERS WITH SIMILAR TASTE...")
print("="*60)

similarities = {}

for user, their_ratings in user_ratings.items():
    common_movies = []
    for movie in your_ratings:
        if movie in their_ratings:
            common_movies.append(movie)
    if len(common_movies) > 0:
        same_count = 0
        for movie in common_movies:
            if your_ratings[movie] == their_ratings[movie]:
                same_count += 1
        similarity = (same_count / len(common_movies)) * 100
        similarities[user] = similarity

sorted_users = sorted(similarities.items(), key=lambda x: x[1], reverse=True)

print("\n✅ TOP 5 USERS WITH SIMILAR TASTE:")
for user, score in sorted_users[:5]:
    print(f"  User {user}: {score:.0f}% match")

print("\n" + "="*60)
print("🎭 FILTER BY GENRE? (Optional)")
print("="*60)
print("Available genres: Action, Adventure, Animation, Comedy, Crime,")
print("Drama, Fantasy, Horror, Romance, Sci-Fi, Thriller, and more")

filter_choice = input("\nFilter by genre? (Enter genre or press Enter to skip): ").strip()

movie_genres = {}
with open('movies.csv', 'r', encoding='utf-8') as file:
    next(file)
    for line in file:
        parts = line.strip().split(',', 2)
        if len(parts) >= 3:
            movie_id = parts[0]
            title = parts[1]
            genres = parts[2] if len(parts) > 2 else ""
            if movie_id in movies:
                movie_genres[movies[movie_id]] = genres

print("\n" + "="*60)
print("🎬 TOP 10 RECOMMENDATIONS FOR YOU:")
print("="*60)

recommendations = []

for user, similarity in sorted_users[:5]:
    their_ratings = user_ratings[user]
    for movie, rating in their_ratings.items():
        if movie not in your_ratings:
            if rating >= 4:
                recommendations.append((movie, rating, user, similarity))

recommendations.sort(key=lambda x: x[1], reverse=True)

if filter_choice:
    print(f"\n🔍 Filtering for {filter_choice} movies...")
    filtered_recs = []
    for movie, rating, user, similarity in recommendations:
        if movie in movie_genres:
            if filter_choice.lower() in movie_genres[movie].lower():
                filtered_recs.append((movie, rating, user, similarity))
    recommendations = filtered_recs
    print(f"✅ Found {len(recommendations)} {filter_choice} recommendations")

if len(recommendations) == 0:
    print("\n❌ No recommendations found! Try rating more movies!")
else:
    seen_movies = set()
    count = 0
    for movie, rating, user, similarity in recommendations:
        if movie not in seen_movies:
            seen_movies.add(movie)
            count += 1
            print(f"\n{count}. {movie}")
            print(f"   Rating: {'⭐' * int(rating)} ({rating} stars)")
            print(f"   Recommended by: User {user} ({similarity:.0f}% match)")
            if count >= 10:
                break

print("\n" + "="*60)
print("💡 WHY THESE RECOMMENDATIONS?")
print("="*60)

if len(recommendations) > 0:
    top_rec = recommendations[0]
    top_movie = top_rec[0]
    top_rating = top_rec[1]
    print(f"\n🎯 Let's explain: '{top_movie}'")
    print("-"*60)
    recommenders = []
    for movie, rating, user, similarity in recommendations:
        if movie == top_movie:
            recommenders.append((user, similarity, rating))
    print(f"\n👥 Recommended by {len(recommenders)} similar user(s):")
    for user, similarity, rating in recommenders[:3]:
        print(f"\n  User {user} ({similarity:.0f}% match):")
        print(f"    • Rated '{top_movie}': {rating} stars")
        common = []
        for your_movie, your_rating in your_ratings.items():
            if your_movie in user_ratings[user]:
                if your_ratings[your_movie] == user_ratings[user][your_movie]:
                    common.append(your_movie)
        if common:
            print(f"    • You both loved: {', '.join(common[:3])}")
            if len(common) > 3:
                print(f"      ...and {len(common)-3} more movies")

print("\n💾 Saving results to file...")

with open('recommendations.txt', 'w', encoding='utf-8') as f:
    f.write("="*60 + "\n")
    f.write("🎬 YOUR PERSONALIZED MOVIE RECOMMENDATIONS\n")
    f.write("="*60 + "\n\n")
    f.write("YOUR RATINGS:\n")
    f.write("-"*60 + "\n")
    for movie, rating in your_ratings.items():
        f.write(f"  {movie}: {'⭐' * int(rating)} ({rating} stars)\n")
    f.write("\n" + "="*60 + "\n")
    f.write("TOP SIMILAR USERS:\n")
    f.write("-"*60 + "\n")
    for user, score in sorted_users[:5]:
        f.write(f"  User {user}: {score:.0f}% match\n")
    f.write("\n" + "="*60 + "\n")
    f.write("TOP 10 RECOMMENDATIONS:\n")
    f.write("-"*60 + "\n")
    seen_movies_file = set()
    count_file = 0
    for movie, rating, user, similarity in recommendations:
        if movie not in seen_movies_file and count_file < 10:
            seen_movies_file.add(movie)
            count_file += 1
            f.write(f"\n{count_file}. {movie}\n")
            f.write(f"   Rating: {'⭐' * int(rating)} ({rating} stars)\n")
            f.write(f"   Recommended by: User {user} ({similarity:.0f}% match)\n")
    f.write("\n" + "="*60 + "\n")

print("✅ Results saved to 'recommendations.txt'")

print("\n" + "="*60)
print("✅ DONE! Enjoy watching!")
print("="*60)