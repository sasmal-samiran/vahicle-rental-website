from rest_framework import status, generics, permissions, parsers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q
from .models import User
from .serializers import (
    UserSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    PasswordLoginSerializer,
    CustomerRegistrationSerializer
)
from .services import OTPService

class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CustomerRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        refresh['role'] = user.role
        refresh['username'] = user.username

        return Response({
            'detail': 'Account registered successfully!',
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)

class RequestOTPView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data['identifier'].strip()
        purpose = serializer.validated_data.get('purpose', 'LOGIN')

        user = User.objects.filter(Q(phone_number=identifier) | Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()

        if purpose == 'LOGIN' and not user:
            return Response({
                'error': 'No account found with this phone number or email. Please register first.'
            }, status=status.HTTP_404_NOT_FOUND)

        if purpose == 'REGISTER' and user:
            return Response({
                'error': 'An account already exists with this phone number or email. Please sign in.'
            }, status=status.HTTP_400_BAD_REQUEST)

        otp_record = OTPService.generate_otp(identifier, purpose=purpose, user=user)

        return Response({
            'detail': f'Verification code sent to {identifier}',
            'identifier': identifier,
            'purpose': purpose,
            'dev_otp': otp_record.otp_code,
            'expires_in_seconds': 300
        }, status=status.HTTP_200_OK)

class VerifyOTPView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        identifier = serializer.validated_data['identifier'].strip()
        otp_code = serializer.validated_data['otp_code'].strip()
        purpose = serializer.validated_data.get('purpose', 'LOGIN')

        success, message = OTPService.verify_otp(identifier, otp_code, purpose)
        if not success:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(Q(phone_number=identifier) | Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()
        
        if not user:
            if purpose in ['REGISTER', 'VERIFY']:
                return Response({
                    'detail': 'OTP verified successfully.',
                    'verified': True,
                    'identifier': identifier
                }, status=status.HTTP_200_OK)
            return Response({
                'error': 'Account not found. Please register first.'
            }, status=status.HTTP_404_NOT_FOUND)

        if not user.is_active:
            return Response({
                'error': 'Account is disabled. Please contact support.'
            }, status=status.HTTP_403_FORBIDDEN)

        if '@' not in identifier:
            user.is_phone_verified = True
            user.save(update_fields=['is_phone_verified'])

        refresh = RefreshToken.for_user(user)
        refresh['role'] = user.role
        refresh['username'] = user.username

        return Response({
            'detail': 'Authentication successful',
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)

class PasswordLoginView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username_or_phone = serializer.validated_data['username_or_phone'].strip()
        password = serializer.validated_data['password']

        user = User.objects.filter(
            Q(username=username_or_phone) | Q(phone_number=username_or_phone) | Q(email=username_or_phone)
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                return Response({'error': 'Account is disabled. Please contact support.'}, status=status.HTTP_403_FORBIDDEN)
            
            refresh = RefreshToken.for_user(user)
            refresh['role'] = user.role
            refresh['username'] = user.username

            return Response({
                'detail': 'Login successful',
                'user': UserSerializer(user, context={'request': request}).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid username/phone or password.'}, status=status.HTTP_401_UNAUTHORIZED)

class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        user = serializer.save()
        profile_picture_file = self.request.FILES.get('profile_picture') or self.request.FILES.get('profile_image')
        
        # Check if profile picture was explicitly cleared
        remove_picture = (
            self.request.data.get('profile_picture') == '' or
            self.request.data.get('remove_profile_picture') in [True, 'true', '1']
        )

        from utils.supabase_storage import SupabaseStorageService
        if profile_picture_file:
            old_path = user.profile_image_path
            new_path = SupabaseStorageService.upload_profile_image(user.id, profile_picture_file)
            user.profile_image_path = new_path
            user.save(update_fields=['profile_image_path', 'updated_at'])
            if old_path and old_path != new_path:
                SupabaseStorageService.delete_profile_image(old_path)
        elif remove_picture and user.profile_image_path:
            SupabaseStorageService.delete_profile_image(user.profile_image_path)
            user.profile_image_path = None
            user.save(update_fields=['profile_image_path', 'updated_at'])

class AdminCustomerListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = User.objects.filter(role='CUSTOMER').order_by('-created_at')
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(email__icontains=search)
            )
        return queryset

class AdminCustomerToggleStatusView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk):
        try:
            customer = User.objects.get(pk=pk, role='CUSTOMER')
            customer.is_active = not customer.is_active
            customer.save()
            status_text = 'activated' if customer.is_active else 'deactivated'
            return Response({
                'detail': f'Customer account {status_text}.',
                'is_active': customer.is_active
            })
        except User.DoesNotExist:
            return Response({'error': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)
