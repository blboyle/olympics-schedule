import json
from datetime import datetime, timedelta

from playwright.sync_api import sync_playwright

from .models import Country, Discipline, Event, Venue

BASE_URL = "https://www.olympics.com/wmr-owg2026"
SCHEDULE_URL = f"{BASE_URL}/schedules/api/ENG/schedule/lite/day"
DISCIPLINES_URL = f"{BASE_URL}/info/api/ENG/disciplinesevents"
VENUES_URL = f"{BASE_URL}/info/api/ENG/venues"
NOCS_URL = f"{BASE_URL}/info/api/ENG/nocs"

START_DATE = datetime(2026, 2, 6)
END_DATE = datetime(2026, 2, 22)


def fetch_json(page, url):
    """Navigate to URL and extract JSON from page content."""
    page.goto(url, wait_until="networkidle")
    content = page.locator("body").inner_text()
    return json.loads(content)


def parse_datetime(dt_str):
    """Parse ISO datetime string to timezone-aware datetime."""
    if not dt_str:
        return None
    return datetime.fromisoformat(dt_str)


def fetch_all_data_from_api():
    """Fetch all data from Olympics API using Playwright. Returns raw data."""
    print("Fetching data from Olympics API...")

    all_data = {
        "disciplines": [],
        "venues": [],
        "countries": [],
        "schedule": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 720},
        )
        page = context.new_page()

        # Fetch disciplines
        print("  Disciplines...", end=" ", flush=True)
        data = fetch_json(page, DISCIPLINES_URL)
        all_data["disciplines"] = data.get("disciplines", [])
        print(f"{len(all_data['disciplines'])} found")

        # Fetch venues
        print("  Venues...", end=" ", flush=True)
        data = fetch_json(page, VENUES_URL)
        all_data["venues"] = data.get("venues", [])
        print(f"{len(all_data['venues'])} found")

        # Fetch countries
        print("  Countries...", end=" ", flush=True)
        data = fetch_json(page, NOCS_URL)
        all_data["countries"] = data.get("nocs", [])
        print(f"{len(all_data['countries'])} found")

        # Fetch schedule for each day
        print("  Schedule:")
        current = START_DATE
        while current <= END_DATE:
            date_str = current.strftime("%Y-%m-%d")
            print(f"    {date_str}...", end=" ", flush=True)
            try:
                url = f"{SCHEDULE_URL}/{date_str}"
                data = fetch_json(page, url)
                units = data.get("units", [])
                all_data["schedule"].extend(units)
                print(f"{len(units)} events")
            except Exception as e:
                print(f"error: {e}")
            current += timedelta(days=1)

        browser.close()

    print(f"Total events fetched: {len(all_data['schedule'])}")
    return all_data


def save_data_to_db(all_data):
    """Save fetched data to database."""
    print("Saving to database...")

    # Save disciplines
    for disc in all_data["disciplines"]:
        Discipline.objects.update_or_create(
            code=disc["id"],
            defaults={"name": disc["name"]},
        )
    print(f"  {len(all_data['disciplines'])} disciplines")

    # Save venues
    for venue in all_data["venues"]:
        Venue.objects.update_or_create(
            code=venue["id"],
            defaults={
                "name": venue["name"],
                "short_name": venue["name"],
            },
        )
    print(f"  {len(all_data['venues'])} venues")

    # Save countries
    for noc in all_data["countries"]:
        Country.objects.update_or_create(
            code=noc["id"],
            defaults={
                "name": noc["name"],
                "continent": noc.get("continent", ""),
            },
        )
    print(f"  {len(all_data['countries'])} countries")

    # Save events
    event_count = 0
    for unit in all_data["schedule"]:
        disc_code = unit.get("disciplineCode")
        discipline = Discipline.objects.filter(code=disc_code).first()
        if not discipline:
            continue

        venue_code = unit.get("venue")
        venue = Venue.objects.filter(code=venue_code).first()

        status = unit.get("status", "SCHEDULED")
        if status not in ["SCHEDULED", "RUNNING", "FINISHED", "CANCELLED"]:
            status = "SCHEDULED"

        competitors_data = unit.get("competitors", [])
        competitor_nocs = [c.get("noc") for c in competitors_data if c.get("noc")]

        event, _ = Event.objects.update_or_create(
            id=unit["id"],
            defaults={
                "discipline": discipline,
                "event_name": unit.get("eventName", ""),
                "unit_name": unit.get("eventUnitName", ""),
                "start_time": parse_datetime(unit.get("startDate")),
                "end_time": parse_datetime(unit.get("endDate")),
                "venue": venue,
                "location": unit.get("locationShortDescription", ""),
                "status": status,
                "is_live": unit.get("liveFlag", False),
                "is_medal_event": unit.get("medalFlag", 0) == 1,
                "competitors_json": competitors_data,
            },
        )

        event.competitors.clear()
        for noc in competitor_nocs:
            country = Country.objects.filter(code=noc).first()
            if country:
                event.competitors.add(country)

        event_count += 1

    print(f"  {event_count} events")
    return event_count


def fetch_all_schedule():
    """Fetch complete schedule and save to database."""
    print("Starting Olympics schedule refresh...")
    all_data = fetch_all_data_from_api()
    count = save_data_to_db(all_data)
    print(f"Done! {count} events saved.")
    return count
