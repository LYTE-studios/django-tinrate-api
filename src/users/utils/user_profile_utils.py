# user_profile_utils.py

def calculate_average_rating(reviews):
    """
    Calculate the average rating from a queryset of reviews.
    Excludes reviews with null ratings.
    """
    reviews = reviews.exclude(rating__isnull=True)
    average = round(sum(review.rating for review in reviews) / reviews.count(), 2) if reviews else 0
    return average