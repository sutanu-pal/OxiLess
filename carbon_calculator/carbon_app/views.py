from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
import requests
import json
import logging
from .forms import CarbonForm, GroupForm, JoinGroupForm
from .models import CarbonSubmission, UserProfile, Group
from django.db.models import Sum
from django.db import transaction
import os
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json

import os



logger = logging.getLogger(__name__)

def landing_page(request):
   
    logger.info("Entering landing_page view")
    
    if request.user.is_authenticated:
        logger.info(f"Authenticated user {request.user.email} redirected to home")
        return redirect('home')
    
    logger.info("Rendering landing_page.html for unauthenticated user")
    return render(request, 'landing_page.html')



@login_required
def home(request):
    
    form = CarbonForm()
    logger.info("Entering home view")

    if request.method == 'POST':
        logger.info("POST request received")
        form = CarbonForm(request.POST)
        if form.is_valid():
            logger.info("Form is valid")
            try:
                with transaction.atomic():
                    data = form.cleaned_data
                    logger.info(f"Form data: {data}")
                    total_emissions = 0
                    emission_breakdown = {}

                    # Google Gemini API configuration for emissions calculation
                    GOOGLE_API_KEY = 'AIzaSyD7d9Ju1YIKixpL4QrUkrksCGODAYAB9oc'
                    gemini_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'
                    headers = {'Content-Type': 'application/json'}
                    emissions_payload = {
                        "contents": [{
                            "parts": [{
                                "text": (
                                    f"Estimate the carbon footprint (in kg CO2e) for a user in {data['region']} with the following data: "
                                    f"Electricity usage: {data['electricity_kwh']} kWh, "
                                    f"Transport: {data['transport_km']} km using {data['vehicle_type']}, "
                                    f"Flights: {data['flights_per_year']} flights per year (class: {data['flight_class']}, assume 1000 km per flight), "
                                    f"Grocery spending: ${data['grocery_spend']} (diet type: {data['diet_type']}), "
                                    f"Other purchases: ${data['purchase_spend']} (category: {data['purchase_category']}), "
                                    f"Home type: {data['home_type']}, Household size: {data['household_size']}. "
                                    "Return a JSON object with keys 'electricity', 'transport', 'flights', 'food', 'purchases', and 'total' (sum of all categories). "
                                    "Wrap the JSON in ```json\n...\n```."
                                )
                            }]
                        }]
                    }

                    # Call Gemini API for emissions calculation
                    logger.info("Calling Gemini API for emissions")
                    response = requests.post(
                        f"{gemini_url}?key={GOOGLE_API_KEY}",
                        json=emissions_payload,
                        headers=headers,
                        timeout=10
                    )
                    logger.info(f"Gemini emissions response status: {response.status_code}")
                    if response.status_code != 200:
                        logger.error(f"Gemini API error (emissions): {response.text}")
                        messages.error(request, "Error calculating emissions. Please try again.")
                        return render(request, 'home.html', {'form': form})

                    response_data = response.json()['candidates'][0]['content']['parts'][0]['text']
                    logger.info(f"Gemini emissions response: {response_data}")
                    try:
                        # Extract JSON from ```json\n...\n``` block
                        json_start = response_data.find('```json\n') + 8
                        json_end = response_data.rfind('\n```')
                        if json_start > 7 and json_end > json_start:
                            response_data = response_data[json_start:json_end]
                        emissions_data = json.loads(response_data)
                        emission_breakdown = {
                            'electricity': float(emissions_data.get('electricity', 0)),
                            'transport': float(emissions_data.get('transport', 0)),
                            'flights': float(emissions_data.get('flights', 0)),
                            'food': float(emissions_data.get('food', 0)),
                            'purchases': float(emissions_data.get('purchases', 0))
                        }
                        total_emissions = float(emissions_data.get('total', sum(emission_breakdown.values())))
                        logger.info(f"Parsed emissions: {emission_breakdown}, Total: {total_emissions}")
                    except (json.JSONDecodeError, ValueError, TypeError, KeyError) as e:
                        logger.error(f"Error parsing Gemini emissions response: {str(e)}")
                        messages.error(request, "Error processing emissions data. Please try again.")
                        return render(request, 'home.html', {'form': form})

                    # Award XP
                    profile = UserProfile.objects.get(user=request.user)
                    profile.xp_points += 50
                    previous_submission = CarbonSubmission.objects.filter(user=request.user).order_by('-created_at').first()
                    if previous_submission and total_emissions < previous_submission.total_emissions:
                        profile.xp_points += 100
                    profile.save()
                    logger.info("XP awarded and profile saved")

                    # Update leaderboards
                    if profile.group:
                        group_xp = UserProfile.objects.filter(group=profile.group).aggregate(Sum('xp_points'))['xp_points__sum'] or 0
                        profile.group.xp_points = group_xp
                        profile.group.save()
                        logger.info("Leaderboard updated")

                    # Save submission
                    submission = CarbonSubmission(
                        user=request.user,
                        electricity_kwh=data['electricity_kwh'],
                        region=data['region'],
                        transport_km=data['transport_km'],
                        vehicle_type=data['vehicle_type'],
                        flights_per_year=data['flights_per_year'],
                        flight_class=data['flight_class'],
                        grocery_spend=data['grocery_spend'],
                        diet_type=data['diet_type'],
                        purchase_spend=data['purchase_spend'],
                        purchase_category=data['purchase_category'],
                        home_type=data['home_type'],
                        household_size=data['household_size'],
                        total_emissions=total_emissions
                    )
                    submission.save()
                    logger.info("Submission saved")

                    # Call Gemini API for suggestions
                    logger.info("Calling Gemini API for suggestions")
                    suggestions_payload = {
                        "contents": [{
                            "parts": [{
                                "text": (
                                    f"Given a carbon footprint with breakdown: {json.dumps(emission_breakdown)} kg CO2e for a user in {data['region']}, "
                                    "suggest specific actions to reduce emissions. Return a list of suggestions as plain text, one per line."
                                )
                            }]
                        }]
                    }
                    response = requests.post(
                        f"{gemini_url}?key={GOOGLE_API_KEY}",
                        json=suggestions_payload,
                        headers=headers,
                        timeout=10
                    )
                    logger.info(f"Gemini suggestions response status: {response.status_code}")
                    if response.status_code != 200:
                        logger.error(f"Gemini API error (suggestions): {response.text}")
                        suggestions = ["Error fetching suggestions."]
                    else:
                        suggestions_text = response.json()['candidates'][0]['content']['parts'][0]['text']
                        suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip()] or ["No suggestions available."]
                        logger.info(f"Suggestions: {suggestions}")

                    logger.info("Rendering results.html")
                    return render(request, 'results.html', {
                        'total_emissions': round(total_emissions, 2),
                        'emission_breakdown': emission_breakdown,
                        'suggestions': suggestions,
                        'xp_points': profile.xp_points
                    })
            except Exception as e:
                logger.error(f"Home view error: {str(e)}")
                messages.error(request, "An unexpected error occurred. Please try again.")
                return render(request, 'home.html', {'form': form})
        else:
            logger.info("Form is invalid")
            messages.error(request, "Invalid form data. Please try again.")
            return render(request, 'home.html', {'form': form})

    logger.info("Rendering home.html for GET request")
    context = {
        'form': form,
        'user': request.user,
    }
    return render(request, 'home.html', context)

@login_required
def leaderboard(request):
    try:
        individual_leaderboard = UserProfile.objects.order_by('-xp_points')[:10].values('user__email', 'xp_points')
        individual_ranking = [(profile['user__email'], profile['xp_points']) for profile in individual_leaderboard]
        group_leaderboard = Group.objects.filter(xp_points__gt=0).order_by('-xp_points')[:10].values('name', 'xp_points')
        group_ranking = [(group['name'], group['xp_points']) for group in group_leaderboard]
        return render(request, 'leaderboard.html', {
            'individual_leaderboard': individual_ranking,
            'group_leaderboard': group_ranking
        })
    except Exception as e:
        logger.error(f"Leaderboard error: {str(e)}")
        messages.error(request, "Error loading leaderboard.")
        return render(request, 'leaderboard.html', {'individual_leaderboard': [], 'group_leaderboard': []})

@login_required
def group_create(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    group = Group.objects.create(name=form.cleaned_data['name'])
                    profile = UserProfile.objects.get(user=request.user)
                    profile.group = group
                    profile.xp_points += 20
                    profile.save()
                    join_url = request.build_absolute_uri(reverse('group_join') + f"?code={group.code}")
                    whatsapp_url = f"https://wa.me/?text=Join my carbon competition group '{group.name}': {join_url}"
                    messages.success(request, f"Group '{group.name}' created! Share: <a href='{whatsapp_url}'>WhatsApp</a> | Link: {join_url}")
                    logger.info(f"User {request.user.email} created group {group.name} with code {group.code}")
                    return redirect('home')
            except Exception as e:
                logger.error(f"Group create error: {str(e)}")
                messages.error(request, "Error creating group.")
    else:
        form = GroupForm()
    return render(request, 'group_create.html', {'form': form})

@login_required
def group_join(request):
    code = request.GET.get('code', '')
    initial = {'code': code} if code else {}
    if request.method == 'POST':
        form = JoinGroupForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    group = Group.objects.get(code=form.cleaned_data['code'])
                    profile = UserProfile.objects.get(user=request.user)
                    if profile.group:
                        messages.error(request, "You are already in a group.")
                        return render(request, 'group_join.html', {'form': form})
                    profile.group = group
                    profile.xp_points += 20
                    if code:
                        inviter = UserProfile.objects.filter(group=group, user__is_active=True).exclude(user=request.user).first()
                        if inviter:
                            profile.invited_by = inviter.user
                            inviter.xp_points += 20
                            inviter.save()
                    profile.save()
                    group_xp = UserProfile.objects.filter(group=group).aggregate(Sum('xp_points'))['xp_points__sum'] or 0
                    group.xp_points = group_xp
                    group.save()
                    messages.success(request, f"Joined group '{group.name}'!")
                    logger.info(f"User {request.user.email} joined group {group.name} with code {group.code}")
                    return redirect('home')
            except Group.DoesNotExist:
                messages.error(request, "Invalid group code.")
                return render(request, 'group_join.html', {'form': form})
            except Exception as e:
                logger.error(f"Group join error: {str(e)}")
                messages.error(request, "Error joining group.")
                return render(request, 'group_join.html', {'form': form})
    else:
        form = JoinGroupForm(initial=initial)
    return render(request, 'group_join.html', {'form': form})

@login_required
def previous_scores(request):
    
    logger.info(f"Entering previous_scores view for user {request.user.email}")
    try:
        # Fetch user's submissions, ordered by newest first
        submissions = CarbonSubmission.objects.filter(user=request.user).order_by('-created_at')
        logger.info(f"Retrieved {submissions.count()} submissions for user {request.user.email}")

        # Fetch user's profile for total XP
        profile = UserProfile.objects.get(user=request.user)
        total_xp = profile.xp_points
        logger.info(f"Total XP for user {request.user.email}: {total_xp}")

        context = {
            'submissions': submissions,
            'total_xp': total_xp,
        }
        return render(request, 'previous_scores.html', context)
    except UserProfile.DoesNotExist:
        logger.error(f"UserProfile not found for user {request.user.email}")
        messages.error(request, "User profile not found. Please contact support.")
        return redirect('home')
    except Exception as e:
        logger.error(f"Previous scores view error: {str(e)}")
        messages.error(request, "An error occurred while loading your scores.")
        return redirect('home')


from django.contrib.auth import logout

def user_logout(request):
    logger.info(f"User {request.user.email} logging out")
    logout(request)
    return redirect('landing_page')