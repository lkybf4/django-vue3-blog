from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import os
import uuid
from django.conf import settings


class ImageUploadView(APIView):
    """图片上传视图"""
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if 'image' not in request.FILES:
            return Response(
                {'error': '没有上传图片'},
                status=status.HTTP_400_BAD_REQUEST
            )

        image = request.FILES['image']
        
        # 验证文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if image.content_type not in allowed_types:
            return Response(
                {'error': '不支持的图片格式，仅支持 JPG、PNG、GIF、WebP'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 验证文件大小（最大 5MB）
        max_size = 5 * 1024 * 1024  # 5MB
        if image.size > max_size:
            return Response(
                {'error': '图片大小不能超过 5MB'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 生成唯一文件名
        ext = image.name.split('.')[-1]
        filename = f"{uuid.uuid4().hex}.{ext}"
        
        # 获取当前年月
        from datetime import datetime
        now = datetime.now()
        
        # 1. 先拼接出正确的保存目录（比如 media/uploads/2026/10/）
        upload_dir = os.path.join(
            settings.MEDIA_ROOT, 
            'uploads', 
            str(now.year), 
            f"{now.month:02d}"
        )
        # 确保这个真实路径存在（exist_ok=True 防止重复创建报错）
        os.makedirs(upload_dir, exist_ok=True)
        
        # 2. 拼出完整的文件绝对路径
        upload_path = os.path.join(upload_dir, filename)
        
        # 3. 写入文件
        with open(upload_path, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)
        
        # 4. 返回给前端的相对 URL（注意这里也统一格式）
        image_url = f"{settings.MEDIA_URL}uploads/{now.year}/{now.month:02d}/{filename}"
        
        return Response({
            'url': image_url,
            'filename': filename,
            'size': image.size
        }, status=status.HTTP_201_CREATED)