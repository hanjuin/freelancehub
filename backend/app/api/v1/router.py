from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    availability,
    bookings,
    customers,
    freelancers,
    invoices,
    notifications,
    payments,
    public,
    reviews,
    services,
    settings,
    staff,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(freelancers.router)
api_router.include_router(services.router)
api_router.include_router(staff.router)
api_router.include_router(availability.router)
api_router.include_router(bookings.router)
api_router.include_router(customers.router)
api_router.include_router(invoices.router)
api_router.include_router(payments.router)
api_router.include_router(reviews.router)
api_router.include_router(notifications.router)
api_router.include_router(settings.router)
api_router.include_router(public.router)
