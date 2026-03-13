from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import House, HouseMember
import uuid


# ==================== House APIs ====================

class HouseListCreateView(APIView):
    """
    GET /api/houses - List all houses where user is a member
    POST /api/houses - Create a new house, creator becomes owner
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get list of houses where the user is a member"""
        memberships = HouseMember.objects.filter(user=request.user).select_related('house')
        houses = []
        for membership in memberships:
            houses.append({
                'id': str(membership.house.id),
                'house_name': membership.house.house_name,
                'address': membership.house.address,
                'lat': membership.house.lat,
                'long': membership.house.long,
                'role': membership.role,
                'emoji':membership.house.emoji,
                'created_at': membership.house.created_at.isoformat(),
            })
        return Response(houses, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new house, creator becomes owner"""
        house_name = request.data.get('house_name')
        address = request.data.get('address')
        lat = request.data.get('lat')
        long = request.data.get('long')
        emoji = request.data.get('emoji', '🏠')

        if not house_name:
            return Response(
                {'error': 'house_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not address:
            return Response(
                {'error': 'address is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create house
        house = House.objects.create(
            house_name=house_name,
            address=address,
            lat=lat,
            long=long,
            emoji=emoji,
        )

        # Create owner membership
        HouseMember.objects.create(
            house=house,
            user=request.user,
            role='owner'
        )

        return Response({
            'id': str(house.id),
            'house_name': house.house_name,
            'address': house.address,
            'lat': house.lat,
            'long': house.long,
            'emoji': house.emoji,
            'role': 'owner',
            'created_at': house.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)


class HouseDetailView(APIView):
    """
    GET /api/house/:id - Get house details
    PATCH /api/house/:id - Update house
    DELETE /api/house/:id - Delete house
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, house_id, user):
        """Get house and check membership"""
        try:
            house = House.objects.get(id=house_id)
            membership = HouseMember.objects.get(house=house, user=user)
            return house, membership
        except (House.DoesNotExist, HouseMember.DoesNotExist):
            return None, None

    def get(self, request, house_id):
        """Get house details"""
        house, membership = self.get_object(house_id, request.user)
        
        if not house:
            return Response(
                {'error': 'House not found or you are not a member'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'id': str(house.id),
            'house_name': house.house_name,
            'address': house.address,
            'lat': house.lat,
            'long': house.long,
            'role': membership.role,
            'created_at': house.created_at.isoformat(),
        }, status=status.HTTP_200_OK)

    def patch(self, request, house_id):
        """Update house details"""
        house, membership = self.get_object(house_id, request.user)
        
        if not house:
            return Response(
                {'error': 'House not found or you are not a member'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only owner can update
        if membership.role != 'owner':
            return Response(
                {'error': 'Only owner can update house'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Update fields
        house_name = request.data.get('house_name')
        address = request.data.get('address')
        lat = request.data.get('lat')
        long = request.data.get('long')

        if house_name:
            house.house_name = house_name
        if address:
            house.address = address
        if lat is not None:
            house.lat = lat
        if long is not None:
            house.long = long

        house.save()

        return Response({
            'id': str(house.id),
            'house_name': house.house_name,
            'address': house.address,
            'lat': house.lat,
            'long': house.long,
            'role': membership.role,
            'created_at': house.created_at.isoformat(),
        }, status=status.HTTP_200_OK)

    def delete(self, request, house_id):
        """Delete house"""
        house, membership = self.get_object(house_id, request.user)
        
        if not house:
            return Response(
                {'error': 'House not found or you are not a member'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only owner can delete
        if membership.role != 'owner':
            return Response(
                {'error': 'Only owner can delete house'},
                status=status.HTTP_403_FORBIDDEN
            )

        house.delete()

        return Response(
            {'message': 'House deleted successfully'},
            status=status.HTTP_200_OK
        )


# ==================== User Management APIs ====================

class HouseUserListView(APIView):
    """
    GET /api/houses/:houseId/users - List all members in a house
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, house_id):
        """Get list of members in a house"""
        # Check if user is a member of the house
        membership = HouseMember.objects.filter(
            house_id=house_id,
            user=request.user
        ).first()

        if not membership:
            return Response(
                {'error': 'You are not a member of this house'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all members
        members = HouseMember.objects.filter(house_id=house_id).select_related('user')
        
        result = []
        for member in members:
            result.append({
                'id': str(member.id),
                'user_id': str(member.user.id),
                'username': member.user.username,
                'email': member.user.email,
                'role': member.role,
                'joined_at': member.joined_at.isoformat(),
            })

        return Response(result, status=status.HTTP_200_OK)


class HouseUserInviteView(APIView):
    """
    POST /api/houses/:houseId/users/invite - Invite a user via email
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, house_id):
        """Invite a user to the house via email"""
        # Check if user is owner or admin of the house
        membership = HouseMember.objects.filter(
            house_id=house_id,
            user=request.user
        ).first()

        if not membership or membership.role not in ['owner', 'admin']:
            return Response(
                {'error': 'Only owner or admin can invite users'},
                status=status.HTTP_403_FORBIDDEN
            )

        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get requested role (optional, defaults to member)
        requested_role = request.data.get('role', 'member')
        if requested_role not in ['admin', 'member', 'guest']:
            return Response(
                {'error': 'Role must be admin, member, or guest'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Only owner can invite admin
        if requested_role == 'admin' and membership.role != 'owner':
            return Response(
                {'error': 'Only owner can invite admins'},
                status=status.HTTP_403_FORBIDDEN
            )

        from django.contrib.auth.models import User
        try:
            invited_user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'User with this email does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is already a member
        existing = HouseMember.objects.filter(
            house_id=house_id,
            user=invited_user
        ).first()

        if existing:
            return Response(
                {'error': 'User is already a member of this house'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create membership with specified role
        HouseMember.objects.create(
            house_id=house_id,
            user=invited_user,
            role=requested_role
        )

        house = House.objects.get(id=house_id)
        
        # Send invitation email
        try:
            send_mail(
                subject=f'Invitation to join {house.house_name}',
                message=f'You have been invited to join {house.house_name} as {requested_role}. Accept the invitation to become a member.',
                from_email='noreply@knowwatt.com',
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            pass

        return Response({
            'message': 'User invited successfully',
            'user_id': str(invited_user.id),
            'email': email,
            'role': requested_role,
        }, status=status.HTTP_201_CREATED)


class HouseUserManageView(APIView):
    """
    POST /api/houses/:houseId/users/manage - Manage user (body: {action: 'remove'|'update', user_id, role})
    """
    permission_classes = [IsAuthenticated]

    def get_house_membership(self, house_id, user):
        """Get user's membership in a house"""
        return HouseMember.objects.filter(
            house_id=house_id,
            user=user
        ).first()

    def post(self, request, house_id):
        """Handle member removal or role update"""
        action = request.data.get('action')
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if requester is owner or admin
        requester_membership = self.get_house_membership(house_id, request.user)
        
        if not requester_membership or requester_membership.role not in ['owner', 'admin']:
            return Response(
                {'error': 'Only owner or admin can manage members'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get the target member
        target_membership = HouseMember.objects.filter(
            house_id=house_id,
            user_id=user_id
        ).first()

        if not target_membership:
            return Response(
                {'error': 'Member not found in this house'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Handle remove action
        if action == 'remove':
            # Cannot remove owner
            if target_membership.role == 'owner':
                return Response(
                    {'error': 'Cannot remove owner'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Admin cannot remove another admin
            if requester_membership.role == 'admin' and target_membership.role == 'admin':
                return Response(
                    {'error': 'Admin cannot remove another admin'},
                    status=status.HTTP_403_FORBIDDEN
                )

            target_membership.delete()
            return Response(
                {'message': 'Member removed successfully'},
                status=status.HTTP_200_OK
            )
        
        # Handle update role action
        elif action == 'update_role':
            new_role = request.data.get('role')
            
            # Cannot change owner's role
            if target_membership.role == 'owner':
                return Response(
                    {'error': 'Cannot change owner role'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Admin cannot change another admin's role
            if requester_membership.role == 'admin' and target_membership.role == 'admin':
                return Response(
                    {'error': 'Admin cannot change another admin\'s role'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if new_role not in ['admin', 'member', 'guest']:
                return Response(
                    {'error': 'Role must be admin, member, or guest'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Only owner can assign admin role
            if new_role == 'admin' and requester_membership.role != 'owner':
                return Response(
                    {'error': 'Only owner can assign admin role'},
                    status=status.HTTP_403_FORBIDDEN
                )

            target_membership.role = new_role
            target_membership.save()

            return Response({
                'message': 'Role updated successfully',
                'user_id': str(target_membership.user.id),
                'role': target_membership.role,
            }, status=status.HTTP_200_OK)
        
        else:
            return Response(
                {'error': 'Invalid action. Use "remove" or "update_role"'},
                status=status.HTTP_400_BAD_REQUEST
            )
