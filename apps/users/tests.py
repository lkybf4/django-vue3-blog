from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status


class UserModelTest(TestCase):
    """用户模型测试"""
    
    def test_create_user(self):
        """测试创建用户"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
    
    def test_user_str(self):
        """测试用户字符串表示"""
        user = User.objects.create_user(username='testuser')
        self.assertEqual(str(user), 'testuser')


class UserAPITest(APITestCase):
    """用户 API 测试"""
    
    def setUp(self):
        """测试前准备"""
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/token/'
        self.profile_url = '/api/auth/profile/'
        
        self.user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'password2': 'securepass123'
        }
    
    def test_register_success(self):
        """测试注册成功"""
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'newuser')
    
    def test_register_password_mismatch(self):
        """测试密码不一致"""
        data = self.user_data.copy()
        data['password2'] = 'differentpass'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_duplicate_username(self):
        """测试用户名重复"""
        User.objects.create_user(username='newuser', email='test@example.com', password='pass123')
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_success(self):
        """测试登录成功"""
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_login_invalid_credentials(self):
        """测试登录失败（错误密码）"""
        User.objects.create_user(username='testuser', password='testpass123')
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpass'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_profile_authenticated(self):
        """测试获取用户信息（已登录）"""
        user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
    
    def test_get_profile_unauthenticated(self):
        """测试获取用户信息（未登录）"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
