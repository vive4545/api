from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django_ratelimit.decorators import ratelimit


from .models import User, FriendRequest
from .serializers import UserSerializer, FriendRequestSerializer

class UserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def search(self, request):
        query = request.query_params.get('q', '').lower()
        if query:
            users = User.objects.filter(Q(email__iexact=query) | Q(name__icontains=query))
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        return Response([])

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def signup(self, request):
        email = request.data.get('email').lower()
        password = request.data.get('password')
        if User.objects.filter(email=email).exists():
            return Response({'detail': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(email=email, password=password)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        # Handle login, typically using JWT
        pass

class FriendRequestViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @ratelimit(key='user', rate='3/m', method='POST', block=True)
    @action(detail=False, methods=['post'])
    def send_request(self, request):
        receiver_id = request.data.get('receiver_id')
        try:
            receiver = User.objects.get(id=receiver_id)
            friend_request, created = FriendRequest.objects.get_or_create(
                sender=request.user, receiver=receiver, status='pending'
            )
            if not created:
                return Response({'detail': 'Friend request already sent'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'detail': 'Friend request sent'}, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({'detail': 'Receiver not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def accept_request(self, request):
        request_id = request.data.get('request_id')
        try:
            friend_request = FriendRequest.objects.get(id=request_id, receiver=request.user, status='pending')
            friend_request.status = 'accepted'
            friend_request.save()
            return Response({'detail': 'Friend request accepted'}, status=status.HTTP_200_OK)
        except FriendRequest.DoesNotExist:
            return Response({'detail': 'Friend request not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def reject_request(self, request):
        request_id = request.data.get('request_id')
        try:
            friend_request = FriendRequest.objects.get(id=request_id, receiver=request.user, status='pending')
            friend_request.status = 'rejected'
            friend_request.save()
            return Response({'detail': 'Friend request rejected'}, status=status.HTTP_200_OK)
        except FriendRequest.DoesNotExist:
            return Response({'detail': 'Friend request not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def list_friends(self, request):
        friends = FriendRequest.objects.filter(
            Q(sender=request.user, status='accepted') | Q(receiver=request.user, status='accepted')
        )
        serializer = FriendRequestSerializer(friends, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def list_pending_requests(self, request):
        pending_requests = FriendRequest.objects.filter(receiver=request.user, status='pending')
        serializer = FriendRequestSerializer(pending_requests, many=True)
        return Response(serializer.data)
