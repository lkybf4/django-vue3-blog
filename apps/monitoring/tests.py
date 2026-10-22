"""监控接口权限测试：指标数据只允许管理员读取。"""
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase


class MonitoringPermissionTest(APITestCase):
    def test_anonymous_cannot_read_server_list(self):
        response = self.client.get('/api/monitoring/servers/')
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_anonymous_cannot_read_local_metrics(self):
        response = self.client.get('/api/monitoring/local/')
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_admin_can_read_server_list(self):
        admin = User.objects.create_user(
            username='admin_monitor', password='TestPass123!', is_staff=True
        )
        self.client.force_authenticate(user=admin)
        response = self.client.get('/api/monitoring/servers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_normal_user_cannot_read_server_list(self):
        user = User.objects.create_user(username='normal_monitor', password='TestPass123!')
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/monitoring/servers/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
