from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from apps.vehicles.models import Car, Category
from apps.bookings.models import Booking
from apps.users.models import User
from apps.payments.models import Payment

class AdminDashboardStatsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        total_cars = Car.objects.count()
        available_cars = Car.objects.filter(status='AVAILABLE').count()
        rented_cars = Car.objects.filter(status='RENTED').count()
        maintenance_cars = Car.objects.filter(status='MAINTENANCE').count()

        utilization_rate = round((rented_cars / total_cars * 100), 1) if total_cars > 0 else 0.0

        total_bookings = Booking.objects.count()
        active_rentals = Booking.objects.filter(status='ONGOING').count()
        confirmed_bookings = Booking.objects.filter(status='CONFIRMED').count()
        completed_bookings = Booking.objects.filter(status='COMPLETED').count()
        cancelled_bookings = Booking.objects.filter(status='CANCELLED').count()

        total_revenue_aggr = Booking.objects.filter(payment_status='PAID').aggregate(Sum('total_amount'))['total_amount__sum']
        total_revenue = float(total_revenue_aggr) if total_revenue_aggr else 0.0

        total_customers = User.objects.filter(role='CUSTOMER').count()

        # Monthly Revenue breakdown (Last 6 months)
        now = timezone.now()
        monthly_data = []
        for i in range(5, -1, -1):
            month_date = now - timedelta(days=i*30)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Rough next month
            if month_start.month == 12:
                next_month = month_start.replace(year=month_start.year+1, month=1)
            else:
                next_month = month_start.replace(month=month_start.month+1)

            month_label = month_start.strftime('%b %Y')
            month_rev = Booking.objects.filter(
                payment_status='PAID',
                created_at__gte=month_start,
                created_at__lt=next_month
            ).aggregate(Sum('total_amount'))['total_amount__sum']
            
            month_count = Booking.objects.filter(
                created_at__gte=month_start,
                created_at__lt=next_month
            ).count()

            monthly_data.append({
                'month': month_label,
                'revenue': float(month_rev) if month_rev else 0.0,
                'bookings': month_count
            })

        # Category Breakdown
        categories = Category.objects.annotate(
            total_vehicles=Count('cars'),
            total_rentals=Count('cars__bookings')
        )
        category_breakdown = [
            {
                'name': cat.name,
                'vehicles': cat.total_vehicles,
                'rentals': cat.total_rentals
            }
            for cat in categories
        ]

        # Recent Bookings Feed
        recent_bookings = Booking.objects.select_related('customer', 'car').order_by('-created_at')[:10]
        recent_list = [
            {
                'id': b.id,
                'code': b.booking_code,
                'customer': b.customer.get_full_name() or b.customer.username,
                'car': b.car.display_name,
                'start_date': b.start_date.strftime('%Y-%m-%d'),
                'end_date': b.end_date.strftime('%Y-%m-%d'),
                'total_amount': float(b.total_amount),
                'status': b.status,
                'payment_status': b.payment_status,
                'created_at': b.created_at.strftime('%b %d, %H:%M')
            }
            for b in recent_bookings
        ]

        return Response({
            'kpis': {
                'total_revenue': total_revenue,
                'total_bookings': total_bookings,
                'active_rentals': active_rentals,
                'confirmed_bookings': confirmed_bookings,
                'completed_bookings': completed_bookings,
                'cancelled_bookings': cancelled_bookings,
                'fleet_size': total_cars,
                'available_cars': available_cars,
                'rented_cars': rented_cars,
                'maintenance_cars': maintenance_cars,
                'utilization_rate': utilization_rate,
                'total_customers': total_customers,
            },
            'charts': {
                'monthly_revenue': monthly_data,
                'category_breakdown': category_breakdown,
                'status_distribution': {
                    'CONFIRMED': confirmed_bookings,
                    'ONGOING': active_rentals,
                    'COMPLETED': completed_bookings,
                    'CANCELLED': cancelled_bookings,
                    'PENDING': Booking.objects.filter(status='PENDING').count(),
                }
            },
            'recent_bookings': recent_list
        })
