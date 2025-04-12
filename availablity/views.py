from django.shortcuts import render, redirect
from django.http import JsonResponse
from datetime import datetime, timedelta, time, date 
from django.contrib import messages
from appointments.models import Dentist,Patient,appointment_cancellation,available_timmings
from availablity.models import Dentist_leave
from appointments import urls
from datetime import timedelta, date

def datess(request):
    # Generate next 28 days as 4 weeks (you may already have similar logic)
    today = date.today()
    schedule = []
    for week_index in range(4):
        week = []
        for day_index in range(7):
            d = today + timedelta(days=7*week_index + day_index)
            week.append({
                'date': d.strftime('%Y-%m-%d'),  # Convert date to string
                'day': d.strftime('%A'),
                'clickable': True,  # or your condition
                'selected': False
            })
        schedule.append(week)
    
    return render(request, 'date_selection.html', {
        'schedule': schedule
    })

def date_selector(request, selected_date):
    request.session['date_'] = selected_date

    # Get all dentists
    try:
        dentist_we_got = Dentist.objects.all()
    except Dentist.DoesNotExist:
        messages.error(request, 'No dentist available. Service is temporarily suspended!')
        return redirect('home')

    # Get all dentists on leave for the selected date
    try :
        leave = Dentist_leave.objects.filter(leave_date=selected_date)
        leave_dentist_ids = leave.values_list('dentist_id', flat=True)
    except Dentist_leave.DoesNotExist :
        dentist_on_leave= Dentist.objects.none()
        return render(request, 'select_slots.html', {
        'dentist_on_duty': dentist_we_got,
        'dentist_on_leave': dentist_on_leave
    })
    # Dentists on leave
    dentist_on_leave = Dentist.objects.filter(id__in=leave_dentist_ids)

    # Dentists on duty (not on leave)
    dentist_on_duty = dentist_we_got.exclude(id__in=leave_dentist_ids)

    # Render the page
    return render(request, 'select_slots.html', {
        'dentist_on_duty': dentist_on_duty,
        'dentist_on_leave': dentist_on_leave
    })






    

    
    
    
    

def get_slots(request):

    date_ = request.session.get('date_')
    dentist_id = request.GET.get('dentist_id')

    try:
        selected_date = datetime.strptime(date_, "%Y-%m-%d").date()
        dentist = Dentist.objects.get(id=dentist_id)
    except (ValueError, Dentist.DoesNotExist):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    slot_times = [
        (time(10, 0), time(11, 0)),
        (time(11, 0), time(12, 0)),
        (time(12, 0), time(13, 0)),
        (time(15, 0), time(16, 0)),
        (time(16, 0), time(17, 0)),
        (time(17, 0), time(18, 0)),
    ]

    available_slots = []
    unavailable_slots = []

    for start, end in slot_times:
        slot, created = available_timmings.objects.get_or_create(
            dentist=dentist,
            date=selected_date,
            start_time=start,
            end_time=end,
           
        )

        if slot.is_available():
            available_slots.append(slot)
        else:
            unavailable_slots.append(slot)

    return render(request, '_slots_partial.html', {
        'available_slots': available_slots,
        'unavailable_slots': unavailable_slots,
    })



def book_the_slot(request, dentist_id, start_time, end_time, date, booked_appointments):
    request.session['dentist'] = dentist_id
    request.session['start_time'] = start_time
    request.session['end_time'] = end_time
    request.session['date_'] = date
    request.session['booked_appointments'] = booked_appointments
    return render(request, 'send_otp.html')


# Create your views here.
