from house.models import House, HouseMember


def active_house_context(request):
    """Provide the user's first house as 'active_house' for sidebar navigation."""
    if request.user.is_authenticated:
        membership = (
            HouseMember.objects
            .filter(user=request.user)
            .select_related('house')
            .first()
        )
        if membership:
            return {'active_house': membership.house}
    return {'active_house': None}
