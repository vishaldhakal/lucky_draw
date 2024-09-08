from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from .views import (
    UserRegistrationView, UserLoginView, UserLogoutView, UserProfileView, 
    UserListView, UserDetailView, OrganizationListView, OrganizationDetailView,
    PasswordChangeView, PasswordResetView, PasswordResetConfirmView,GetOrganizationView
)

urlpatterns = [
    # Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    
    # User management
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/profile/', UserProfileView.as_view(), name='user-profile'),
    path('users/change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('users/reset-password/', PasswordResetView.as_view(), name='reset-password'),
    path('users/reset-password-confirm/', PasswordResetConfirmView.as_view(), name='reset-password-confirm'),
    
    # Organization management
    path('organizations/', OrganizationListView.as_view(), name='organization-list'),
    path('organizations/<int:pk>/', OrganizationDetailView.as_view(), name='organization-detail'),
    path('get-organizations/', GetOrganizationView.as_view(), name='get-organizations'),
]