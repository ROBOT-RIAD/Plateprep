from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Task
from .serializers import TaskSerializer
from drf_yasg.utils import swagger_auto_schema
from accounts.permissions import IsAdminOrChef
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.exceptions import MethodNotAllowed
from datetime import datetime

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrChef]
    http_method_names = ['get', 'post', 'patch']
    queryset = Task.objects.all()

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.all() if user.role == 'admin' else (
            Task.objects.filter(assigned_by=user) | Task.objects.filter(assigned_to=user)
        )

        date_str = self.request.query_params.get('date')
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                queryset = queryset.filter(created_at__date=date)  
            except ValueError:
                pass  

        return queryset

    def perform_create(self, serializer):
        serializer.save()

    @swagger_auto_schema(tags=["Tasks"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    



    @swagger_auto_schema(tags=["Tasks"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    



    @swagger_auto_schema(tags=["Tasks"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed('PATCH', detail='Partial update is not allowed. Use update-status action instead.')
    


    @swagger_auto_schema(tags=["Tasks"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    



    @swagger_auto_schema(tags=["Tasks"])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    



    @swagger_auto_schema(tags=["Tasks"])
    @action(detail=False, methods=['get'], url_path='assigned-to-me')
    def assigned_to_me(self, request):
        tasks = Task.objects.filter(assigned_to=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    




    @swagger_auto_schema(tags=["Tasks"])
    @action(detail=False, methods=['get'], url_path='i-assigned')
    def i_assigned(self, request):
        tasks = Task.objects.filter(assigned_by=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    



    @swagger_auto_schema(tags=["Tasks"])
    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        task = self.get_object()
        new_status = request.data.get("status")
        if new_status not in dict(task._meta.get_field("status").choices):
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        task.status = new_status
        task.save()

        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{task.assigned_to.id}",
                {
                    "type": "task_status_update",
                    "task_id": task.id,
                    "new_status": task.status
                }
            )
        except Exception as e:
            print("WebSocket notification failed:", str(e))

        return Response({
            "message": "Status updated successfully.",
            "task_id": task.id,
            "status": task.status
        }, status=status.HTTP_200_OK)
