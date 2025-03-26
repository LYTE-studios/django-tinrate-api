from django.db.models import Avg
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from users.models.profile_models import Review, UserProfile

@receiver(post_save, sender=Review)
def update_profile_rating_on_review_save(sender, instance, created, **kwargs):
    """
    Signal handler that is triggered after a Review instance is saved.
    
    This method recalculates the average rating of the user's profile associated 
    with the review, whether the review is newly created or updated.
    
    Args:
        sender: The model class that triggered the signal (Review).
        instance: The actual instance of the Review being saved.
        created: Boolean flag indicating if the review was newly created (True) 
                 or updated (False).
        **kwargs: Additional keyword arguments passed by the signal.
    
    Updates the 'rating' field of the related UserProfile instance based on the 
    average rating of all associated reviews.
    """
    profile = instance.user_profile
    profile.rating = profile.reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
    profile.save()


@receiver(post_delete, sender=Review)
def update_profile_rating_on_review_delete(sender, instance, **kwargs):
    """
    Signal handler that is triggered after a Review instance is deleted.
    
    This method recalculates the average rating of the user's profile associated 
    with the review after the review is deleted.
    
    Args:
        sender: The model class that triggered the signal (Review).
        instance: The actual instance of the Review being deleted.
        **kwargs: Additional keyword arguments passed by the signal.
    
    Updates the 'rating' field of the related UserProfile instance based on the 
    average rating of all remaining reviews after the review has been deleted.
    """
    profile = instance.user_profile
    profile.rating = profile.reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
    profile.save()