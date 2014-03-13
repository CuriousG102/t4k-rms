from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum, Avg
from datetime import datetime, date, timedelta
import time
from decimal import Decimal
from riders.models import Teammate
from fitness.models import Ride
from durationfield.db.models.fields.duration import DurationField


def all_riders(request):
    #TODO maybe we should write a test
    total_miles = Ride.objects.all().aggregate(Sum('miles'))['miles__sum']
    total_time = Ride.objects.all().aggregate(Sum('duration'))['duration__sum']

    #TODO: doing two database joins, this is probably not a good idea in general
    riders = Teammate.objects
    riders = riders.annotate(total_miles = Sum('ride__miles'))
    riders = riders.annotate(total_time = Sum('ride__duration'))
    riders = riders.order_by('-total_miles')
    context = {
        'riders' : riders,
        'total_miles' : total_miles,
        'total_time' : total_time
    }
    return render(request, 'dashboard/all_riders.html', context)

# Base dashboard view
def dashboard(request, rider=None):

    if rider:
        tm = Teammate.objects.get(pk=rider)
    elif not request.user.is_anonymous():
        tm = request.user
    else:
        return HttpResponseRedirect(reverse('dashboard:login'))

    # Retreive total miles
    rides = Ride.objects.filter(user_id__exact = tm).order_by('-date')
    miles = rides.aggregate(Sum('miles'))
    pace = rides.aggregate(Avg('pace'))
    duration = rides.aggregate(Sum('duration'))

    # Return context
    context = {
        'miles': miles,
        'pace': pace,
        'duration': duration,
        'rides' : rides,
        'rider' : tm,
        'import_date' : date(2014,01,26),
    }

    return render(request, 'dashboard/index.html', context)

def enter_gate(request):
    # Only execute login logic if data is posted
    if request.method == 'POST':
        # Set user variables
        username = request.POST.get('username', False)
        password = request.POST.get('password', False)
        # Authenticate the user
        user = authenticate(username = username, password = password)
        # If the user is a user
        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(reverse('dashboard:dashboard'))
            # If the user isn't active
            else:
                # Return context error message
                context = {
                    'error_message': "You're not an active rider, man."
                }
                return render(request, 'dashboard/login.html', context)
        # If the user doesn't authenticate
        else:
            # Return context error message
            context = {
                'error_message': "Your username and password don't match!"
            }
            return render(request, 'dashboard/login.html', context)
    # If there's no POST data; just a normal login page
    else:
        # Return context w/ no error
        return render(request, 'dashboard/login.html', {})

# Logout view
def exit_gate(request):
    logout(request)
    return redirect('dashboard:dashboard')

# Log a ride
@login_required
def log_ride(request):
    # If the form has been submitted
    if request.method == 'POST':
        # Give the post variables a variable
        buddies = request.POST['partners']
        miles = request.POST['miles']
        pace = request.POST['pace']
        time_logged = request.POST['time']
        comments = request.POST['comments']
        date = request.POST['date']

        new_time = None
        try:
            new_time = time.strptime(time_logged, "%I:%M:%S")
        except ValueError:
            context = {
              'buddies' : buddies,
              'miles' : miles,
              'pace' : pace,
              'comments' : comments,
              'ride_date' : date,
              'time_logged_error' : "Invalid time format. Use HH:MM:SS",
            }
            return render(request, 'dashboard/add_ride.html', context)

        # Set the time to the right format
        h = new_time.tm_hour
        m = new_time.tm_min
        s = new_time.tm_sec

        #TODO do we need to do this
        final_time = (((h*3600)+(m*60)+(s))*1000000)

        # Save into the database
        object = Ride.objects.create(user_id = request.user.id, buddies = buddies,
                date = date, miles = Decimal(miles), pace = Decimal(pace),
                duration = final_time, comments = comments)
        object.save()
        # Return to homepage
        return HttpResponseRedirect(reverse('dashboard:dashboard'))
    else: # Return an normal page
        return render(request, 'dashboard/add_ride.html', {})

# Change user's password
@login_required
def change_password(request):
    # If the form has been submitted
    if request.method == 'POST':
        # Check if the passwords match
        if request.POST['password1'] == request.POST['password2'] and request.POST['password2'] is not None:
            # Change the password
            u = Teammate.objects.get(id__exact = request.user.id)
            u.set_password(request.POST['password2'])
            u.save()
            return HttpResponseRedirect(reverse('dashboard:dashboard'))
        else:
           context = {
               'error_message': "Your passwords don't match!"
           }
           return render(request, 'dashboard/change_password.html', context)
    else: # First time visiting page
        return render(request, 'dashboard/change_password.html', {})

def contest_winners(request):
	#TO DO: This code will crash and burn if there are no teammates in the database
	#TO DO: This code is very verbose and there are many clear ways to cut down on its length, as well as make it easier to modify for new contests
	

	# get all teammates
	teammates = Teammate.objects.all()
	# make a "best" dictionary for comparison purposes. Values are arrays, where the rider with the best performance in that category is stored in index 0 and the rider with the metric for that performance is stored in index 1
	best = {'miles':[None, 0.0], 'avg_speed':[None, 0.0], 'improvement':[None, 0.0]}
	# I define greatest improvement as a fraction. The fraction is (average speed this week)/(average speed overall). Greatest improvement's definition is subject to change.

	for teammate in teammates:
		# get a datetime representing 11:59:59 of the most recent Monday
		currentTime = datetime.today()
		mondayTime = currentTime - timedelta(days = currentTime.weekday())
		mondayTime = mondayTime.replace(hour = 23, minute = 59, second = 59, microsecond = 0)
		# get all rides for that teammate between mondayTime and 7 days earlier
		begin = mondayTime - timedelta(days = 7)
		end = mondayTime
		rides = Ride.objects.filter(date__range=[begin, end])
		rides = rides.filter(user__email = teammate.get_email())

		# find the total time that the rides took
		#duration field is driving me FUCKING NUTS right now so I'm going to take care of this part later

		# find the total miles that the rides covered
		totalMiles = rides.aggregate(Sum('miles'))['miles__sum']

		# find the avg_speed of all the rides for the week
		avgSpeed = rides.aggregate(Avg('pace'))['pace__avg']

		# find the improvement ratio
		rides = Ride.objects.filter(user__email = teammate.get_email())
		overallAvgSpeed = rides.aggregate(Avg('pace'))['pace__avg']
		try:
			improvementRatio = avgSpeed/overallAvgSpeed
		except: # rider has no rides
			improvementRatio = 0

		#compare the values of totalTime, totalMiles, avgSpeed, and improvementRatio for the teammate to those that have been the best so far among their teammates. If they are the best, replace the value for the key they are being compared to with their own name
		
		if best['miles'][0] == None:
			#best['time'][0] = teammate
			#best['time'][1] = totalTime
			best['miles'][0] = teammate
			best['miles'][1] = totalMiles
			best['avg_speed'][0] = teammate
			best['avg_speed'][1] = avgSpeed
			best['improvement'][0] = teammate
			best['improvement'][1] = improvementRatio
		else:
			#if totalTime > best['time'][1]: # this teammate is the best in totalTime
			#	best['time'][0] = teammate
			#	best['time'][1] = totalTime
			if totalMiles > best['miles'][1]:
				best['miles'][0] = teammate
				best['miles'][1] = totalMiles
			if avgSpeed > best['avg_speed'][1]:
				best['avg_speed'][0] = teammate
				best['avg_speed'][1] = avgSpeed
			if improvementRatio > best['improvement'][1]:
				best['improvement'][0] = teammate
				best['improvement'][1] = improvementRatio

	context = {'miles':best['miles'][0], 'avg_speed':best['avg_speed'][0], 'improvement':best['improvement'][0]}

	return render(request, 'dashboard/contest_winners.html', context)



