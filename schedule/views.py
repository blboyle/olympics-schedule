from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .models import Country, Discipline, Event
from .scraper import fetch_all_schedule


@require_GET
def index(request):
    """Main schedule view with filtering."""
    events = Event.objects.select_related("discipline", "venue").prefetch_related(
        "competitors"
    )

    # Get filter values
    discipline_code = request.GET.get("discipline", "")
    country_code = request.GET.get("country", "")
    date_str = request.GET.get("date", "")
    status_filter = request.GET.get("status", "")
    medal_only = request.GET.get("medal") == "1"

    # Apply filters
    if discipline_code:
        events = events.filter(discipline__code=discipline_code)

    if country_code:
        events = events.filter(competitors__code=country_code)

    if date_str:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            events = events.filter(start_time__date=date)
        except ValueError:
            pass

    if status_filter:
        if status_filter == "LIVE":
            events = events.filter(is_live=True)
        elif status_filter == "UPCOMING":
            events = events.filter(status="SCHEDULED")
        elif status_filter == "FINISHED":
            events = events.filter(status="FINISHED")

    if medal_only:
        events = events.filter(is_medal_event=True)

    # Sorting
    sort_by = request.GET.get("sort", "start_time")
    sort_dir = request.GET.get("dir", "asc")

    valid_sorts = ["start_time", "discipline__name", "event_name", "venue__name"]
    if sort_by in valid_sorts:
        if sort_dir == "desc":
            sort_by = f"-{sort_by}"
        events = events.order_by(sort_by)

    # Get filter options
    disciplines = Discipline.objects.all()
    countries = Country.objects.filter(events__isnull=False).distinct()
    dates = (
        Event.objects.dates("start_time", "day")
        if Event.objects.exists()
        else []
    )

    context = {
        "events": events,
        "disciplines": disciplines,
        "countries": countries,
        "dates": dates,
        "current_discipline": discipline_code,
        "current_country": country_code,
        "current_date": date_str,
        "current_status": status_filter,
        "medal_only": medal_only,
        "sort_by": request.GET.get("sort", "start_time"),
        "sort_dir": sort_dir,
    }

    # Return partial for HTMX requests
    if request.headers.get("HX-Request"):
        return render(request, "schedule/_table.html", context)

    return render(request, "schedule/index.html", context)


@require_POST
def refresh(request):
    """Trigger schedule refresh."""
    try:
        count = fetch_all_schedule()
        return HttpResponse(
            f'<div class="alert success">Refreshed {count} events</div>',
            headers={"HX-Trigger": "scheduleRefreshed"},
        )
    except Exception as e:
        return HttpResponse(
            f'<div class="alert error">Error: {e}</div>',
            status=500,
        )
