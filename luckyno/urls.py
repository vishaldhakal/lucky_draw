from django.urls import path
from .views import (
    RewardListCreate,
    RewardRetrieveUpdateDestroy,
    PromoParticipantListCreate,
    PromoParticipantRetrieveUpdateDestroy,
    LuckyCustomerListCreate,
    LuckyCustomerRetrieveUpdateDestroy,
    SelectWinner,
    UploadPromoParticipants,
)

urlpatterns = [
    path("rewards/", RewardListCreate.as_view(), name="reward-list-create"),
    path(
        "rewards/<int:pk>/",
        RewardRetrieveUpdateDestroy.as_view(),
        name="reward-retrieve-update-destroy",
    ),
    path(
        "participants/",
        PromoParticipantListCreate.as_view(),
        name="participant-list-create",
    ),
    path(
        "participants/<int:pk>/",
        PromoParticipantRetrieveUpdateDestroy.as_view(),
        name="participant-retrieve-update-destroy",
    ),
    path(
        "lucky-customers/",
        LuckyCustomerListCreate.as_view(),
        name="lucky-customer-list-create",
    ),
    path(
        "lucky-customers/<int:pk>/",
        LuckyCustomerRetrieveUpdateDestroy.as_view(),
        name="lucky-customer-retrieve-update-destroy",
    ),
    path("select-winner/", SelectWinner.as_view(), name="select-winner"),
    path(
        "upload-participants/",
        UploadPromoParticipants.as_view(),
        name="upload-participants",
    ),
]
