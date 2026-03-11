from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
import uuid
from .models import House, HouseMember  

class HouseModelTests(TestCase):
    """Test House and HouseMember models"""
    
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', email='owner@test.com', password='pass123')
        self.member = User.objects.create_user(username='member', email='member@test.com', password='pass123')
        self.admin = User.objects.create_user(username='admin', email='admin@test.com', password='pass123')
        self.guest = User.objects.create_user(username='guest', email='guest@test.com', password='pass123')
        
        self.house = self.owner.house_set.create(
            house_name='Test House',
            address='123 Test St'
        )
        
        self.owner_membership = self.house.memberships.create(user=self.owner, role='owner')
        self.member_membership = self.house.memberships.create(user=self.member, role='member')
        self.admin_membership = self.house.memberships.create(user=self.admin, role='admin')
        self.guest_membership = self.house.memberships.create(user=self.guest, role='guest')
        
        self.client = APIClient()
        self.token = Token.objects.create(user=self.owner)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')
    
    def test_house_creation(self):
        """Test house model creation"""
        self.assertEqual(self.house.house_name, 'Test House')
        self.assertEqual(self.house.address, '123 Test St')
        self.assertIsNotNone(self.house.id)
    
    def test_house_member_creation(self):
        """Test house member creation"""
        self.assertEqual(self.owner_membership.role, 'owner')
        self.assertEqual(self.member_membership.role, 'member')
        self.assertEqual(self.admin_membership.role, 'admin')
        self.assertEqual(self.guest_membership.role, 'guest')
    
    def test_house_member_unique_together(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            self.house.memberships.create(user=self.owner, role='member')
    
    def test_house_member_permissions(self):
        """Test role-based permissions"""
        # Owner has all permissions
        self.assertTrue(HouseMember.has_permission(self.owner_membership, 'can_create_house'))
        self.assertTrue(HouseMember.has_permission(self.owner_membership, 'can_edit_house'))
        self.assertTrue(HouseMember.has_permission(self.owner_membership, 'can_delete_house'))
        self.assertTrue(HouseMember.has_permission(self.owner_membership, 'can_manage_members'))
        
        # Admin can manage members but not create/edit/delete house
        self.assertFalse(HouseMember.has_permission(self.admin_membership, 'can_create_house'))
        self.assertTrue(HouseMember.has_permission(self.admin_membership, 'can_manage_members'))
        
        # Member can control devices but not manage members
        self.assertTrue(HouseMember.has_permission(self.member_membership, 'can_control_devices'))
        self.assertFalse(HouseMember.has_permission(self.member_membership, 'can_manage_members'))
        
        # Guest can only view
        self.assertTrue(HouseMember.has_permission(self.guest_membership, 'can_view_devices'))
        self.assertFalse(HouseMember.has_permission(self.guest_membership, 'can_control_devices'))


class HouseCRUDTests(TestCase):
    """Test House CRUD endpoints"""
    
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', email='owner@test.com', password='pass123')
        self.member = User.objects.create_user(username='member', email='member@test.com', password='pass123')
        
        self.house = self.owner.house_set.create(
            house_name='Test House',
            address='123 Test St'
        )
        
        self.house.memberships.create(user=self.member, role='member')
        
        self.token = Token.objects.create(user=self.owner)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')
    
    def test_create_house(self):
        """Test creating a new house"""
        response = self.client.post('/api/house/', {
            'house_name': 'New House',
            'address': '456 New St'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['house_name'], 'New House')
        self.assertEqual(response.data['role'], 'owner')
    
    def test_list_houses(self):
        """Test listing houses"""
        response = self.client.get('/api/house/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['house_name'], 'Test House')
        self.assertEqual(response.data[0]['role'], 'owner')
    
    def test_get_house_details(self):
        """Test getting house details"""
        response = self.client.get(f'/api/house/{self.house.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['house_name'], 'Test House')
        self.assertEqual(response.data['role'], 'owner')
    
    def test_get_house_unauthorized(self):
        """Test getting house without membership"""
        member_token = Token.objects.create(user=self.member)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {member_token.key}')
        
        response = self.client.get(f'/api/house/{self.house.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_house(self):
        """Test updating house (owner only)"""
        response = self.client.patch(f'/api/house/{self.house.id}/', {
            'house_name': 'Updated House',
            'address': '789 Updated St'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['house_name'], 'Updated House')
        self.assertEqual(response.data['address'], '789 Updated St')
    
    def test_update_house_forbidden(self):
        """Test updating house as non-owner"""
        member_token = Token.objects.create(user=self.member)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {member_token.key}')
        
        response = self.client.patch(f'/api/house/{self.house.id}/', {
            'house_name': 'Updated House'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_house(self):
        """Test deleting house (owner only)"""
        response = self.client.delete(f'/api/house/{self.house.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'House deleted successfully')
        
        # Verify house is deleted
        self.assertEqual(House.objects.count(), 0)
    
    def test_delete_house_forbidden(self):
        """Test deleting house as non-owner"""
        member_token = Token.objects.create(user=self.member)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {member_token.key}')
        
        response = self.client.delete(f'/api/house/{self.house.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MemberManagementTests(TestCase):
    """Test member management endpoints"""
    
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', email='owner@test.com', password='pass123')
        self.admin = User.objects.create_user(username='admin', email='admin@test.com', password='pass123')
        self.member = User.objects.create_user(username='member', email='member@test.com', password='pass123')
        self.other_member = User.objects.create_user(username='other', email='other@test.com', password='pass123')
        
        self.house = self.owner.house_set.create(
            house_name='Test House',
            address='123 Test St'
        )
        
        self.owner_membership = self.house.memberships.create(user=self.owner, role='owner')
        self.admin_membership = self.house.memberships.create(user=self.admin, role='admin')
        self.member_membership = self.house.memberships.create(user=self.member, role='member')
        self.other_membership = self.house.memberships.create(user=self.other_member, role='member')
        
        self.token = Token.objects.create(user=self.owner)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')
    
    def test_list_members(self):
        """Test listing all members"""
        response = self.client.get(f'/api/houses/{self.house.id}/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
        
        # Check that all members are listed
        usernames = [m['username'] for m in response.data]
        self.assertIn('owner', usernames)
        self.assertIn('admin', usernames)
        self.assertIn('member', usernames)
        self.assertIn('other', usernames)
    
    def test_invite_member(self):
        """Test inviting a member"""
        response = self.client.post(f'/api/houses/{self.house.id}/users/invite/', {
            'email': 'newuser@test.com'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'User invited successfully')
    
    def test_invite_member_with_role(self):
        """Test inviting a member with specific role"""
        response = self.client.post(f'/api/houses/{self.house.id}/users/invite/', {
            'email': 'newadmin@test.com',
            'role': 'admin'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], 'admin')
    
    def test_invite_admin_only_owner(self):
        """Test that only owner can invite admin"""
        admin_token = Token.objects.create(user=self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token.key}')
        
        response = self.client.post(f'/api/houses/{self.house.id}/users/invite/', {
            'email': 'newadmin@test.com',
            'role': 'admin'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_invite_nonexistent_user(self):
        """Test inviting a non-existent user"""
        response = self.client.post(f'/api/houses/{self.house.id}/users/invite/', {
            'email': 'nonexistent@test.com'
        })
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_remove_member(self):
        """Test removing a member"""
        response = self.client.post(f'/api/houses/{self.house.id}/users/manage/', {
            'action': 'remove',
            'user_id': self.member.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify member is removed
        self.assertEqual(self.house.memberships.count(), 3)
        self.assertFalse(self.house.memberships.filter(user=self.member).exists())
    
    def test_remove_owner_forbidden(self):
        """Test that owner cannot be removed"""
        response = self.client.post(f'/api/houses/{self.house.id}/users/manage/', {
            'action': 'remove',
            'user_id': self.owner.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_remove_member_only_admin_can_remove_admin(self):
        """Test that admin cannot remove another admin"""
        admin_token = Token.objects.create(user=self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token.key}')
        
        response = self.client.post(f'/api/houses/{self.house.id}/users/manage/', {
            'action': 'remove',
            'user_id': self.admin.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_change_member_role(self):
        """Test changing a member's role"""
        response = self.client.post(f'/api/houses/{self.house.id}/users/manage/', {
            'action': 'update_role',
            'user_id': self.member.id,
            'role': 'admin'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'admin')
        
        # Verify role is updated
        updated_member = self.house.memberships.get(user=self.member)
        self.assertEqual(updated_member.role, 'admin')
    
    def test_change_role_only_owner_can_assign_admin(self):
        """Test that only owner can assign admin role"""
        admin_token = Token.objects.create(user=self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token.key}')
        
        response = self.client.post(f'/api/houses/{self.house.id}/users/manage/', {
            'action': 'update_role',
            'user_id': self.member.id,
            'role': 'admin'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_change_owner_role_forbidden(self):
        """Test that owner's role cannot be changed"""
        response = self.client.post(f'/api/houses/{self.house.id}/users/manage/', {
            'action': 'update_role',
            'user_id': self.owner.id,
            'role': 'member'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_admin_cannot_change_another_admin_role(self):
        """Test that admin cannot change another admin's role"""
        admin_token = Token.objects.create(user=self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token.key}')
        
        response = self.client.post(f'/api/houses/{self.house.id}/users/manage/', {
            'action': 'update_role',
            'user_id': self.admin.id,
            'role': 'member'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_invalid_action(self):
        """Test handling of invalid action"""
        response = self.client.post(f'/api/houses/{self.house.id}/users/manage/', {
            'action': 'invalid_action',
            'user_id': self.member.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MultiHouseTests(TestCase):
    """Test multi-house scenarios"""
    
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', email='owner@test.com', password='pass123')
        
        self.house1 = self.owner.house_set.create(
            house_name='House 1',
            address='123 St'
        )
        self.owner.memberships.create(user=self.owner, role='owner')
        
        self.house2 = self.owner.house_set.create(
            house_name='House 2',
            address='456 St'
        )
        self.owner.memberships.create(user=self.owner, role='owner')
        
        self.token = Token.objects.create(user=self.owner)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')
    
    def test_list_multiple_houses(self):
        """Test listing all houses for user"""
        response = self.client.get('/api/house/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_user_in_multiple_houses(self):
        """Test that a user can be in multiple houses"""
        member = User.objects.create_user(username='member', email='member@test.com', password='pass123')
        member.memberships.create(house=self.house1, role='member')
        member.memberships.create(house=self.house2, role='member')
        
        member_token = Token.objects.create(user=member)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {member_token.key}')
        
        response = self.client.get('/api/house/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_house_specific_operations(self):
        """Test that operations are specific to a house"""
        member = User.objects.create_user(username='member', email='member@test.com', password='pass123')
        member.memberships.create(house=self.house1, role='member')
        
        member_token = Token.objects.create(user=member)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {member_token.key}')
        
        # Should be able to access house1 but not house2
        response1 = self.client.get(f'/api/house/{self.house1.id}/')
        response2 = self.client.get(f'/api/house/{self.house2.id}/')
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_403_FORBIDDEN)
