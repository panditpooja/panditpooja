import requests
import datetime
import svgwrite
import os
import pytz

# -------------------------------
# CONFIGURATION
# -------------------------------
USERNAME = "panditpooja"  # Your GitHub username
TOKEN = os.environ.get("GH_TOKEN")  # GitHub token from GitHub Actions secret

if not TOKEN:
    print("❌ ERROR: GH_TOKEN is not set as an environment variable.")
    exit(1)

headers = {"Authorization": f"Bearer {TOKEN}"}

# -------------------------------
# TIMEZONE AWARENESS
# -------------------------------
utc = pytz.utc
today_utc = datetime.datetime.now(utc).date()

# -------------------------------
# FETCH ACCOUNT CREATED DATE
# -------------------------------
query_created_at = """
{
  user(login: "%s") {
    createdAt
  }
}
""" % USERNAME

response = requests.post(
    "https://api.github.com/graphql",
    json={"query": query_created_at},
    headers=headers
)

if response.status_code != 200:
    print("❌ GitHub API Error (createdAt)")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    exit(1)

json_response = response.json()
if "errors" in json_response:
    print("❌ GraphQL Error (createdAt)")
    print(json_response["errors"])
    exit(1)

# Parse account creation date
user_data = json_response["data"]["user"]
account_created_at = datetime.datetime.strptime(user_data["createdAt"], "%Y-%m-%dT%H:%M:%SZ").date()

# -------------------------------
# FETCH ALL-TIME CONTRIBUTIONS (year by year)
# -------------------------------
total_contributions = 0
all_days = []
print("📡 Fetching GitHub contribution data year by year...")

year_start = account_created_at
while year_start <= today_utc:
    year_end = min(year_start.replace(year=year_start.year + 1) - datetime.timedelta(days=1), today_utc)
    from_date = year_start.isoformat() + "T00:00:00Z"
    to_date = year_end.isoformat() + "T23:59:59Z"

    query_contributions = """
    {
      user(login: "%s") {
        contributionsCollection(from: "%s", to: "%s") {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """ % (USERNAME, from_date, to_date)

    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query_contributions},
        headers=headers
    )

    if response.status_code != 200:
        print("❌ GitHub API Error (contributions)")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        exit(1)

    json_response = response.json()
    if "errors" in json_response:
        print("❌ GraphQL Error (contributions)")
        print(json_response["errors"])
        exit(1)

    # Parse contribution data for totals and streak calculations
    weeks = json_response["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    for week in weeks:
        for day in week["contributionDays"]:
            count = day["contributionCount"]
            contribution_date = datetime.datetime.strptime(day["date"], "%Y-%m-%d").date()
            total_contributions += count
            all_days.append({
                "date": contribution_date,
                "count": count
            })

    year_start = year_end + datetime.timedelta(days=1)

print(f"✅ Total Contributions: {total_contributions}")
print(f"📅 Today (UTC): {today_utc}")

# -------------------------------
# CALCULATE STREAKS
# -------------------------------
current_streak, longest_streak = 0, 0
current_streak_start, current_streak_end = None, None
longest_streak_start, longest_streak_end = None, None

all_days.sort(key=lambda d: d["date"])  # Ensure days are sorted

temp_streak = 0
temp_start_date = None

# Find longest streak
for day in all_days:
    if day["count"] > 0:
        if temp_streak == 0:
            temp_start_date = day["date"]
        temp_streak += 1

        # Update longest streak if needed
        if temp_streak > longest_streak:
            longest_streak = temp_streak
            longest_streak_start = temp_start_date
            longest_streak_end = day["date"]
    else:
        temp_streak = 0
        temp_start_date = None

# Find current streak (ending at last contribution day)
for i in reversed(range(len(all_days))):
    day = all_days[i]
    if day["count"] > 0:
        if current_streak == 0:
            current_streak_end = day["date"]
            current_streak_start = day["date"]
            current_streak = 1
        else:
            if (current_streak_start - day["date"]).days == 1:
                current_streak_start = day["date"]
                current_streak += 1
            else:
                break
    else:
        if current_streak > 0:
            break

print(f"🔥 Current Streak: {current_streak}")
if current_streak_start and current_streak_end:
    print(f"📆 Current Streak Range: {current_streak_start} - {current_streak_end}")
print(f"🏆 Longest Streak: {longest_streak}")
if longest_streak_start and longest_streak_end:
    print(f"📆 Longest Streak Range: {longest_streak_start} - {longest_streak_end}")

# -------------------------------
# CREATE SVG
# -------------------------------
print("🎨 Generating SVG...")

dwg = svgwrite.Drawing("assets/github-stats.svg", size=("700px", "250px"))

# Colors
background_color = "#181818"
accent_color = "#f57c00"
text_color = "#ffffff"
subtext_color = "#999999"

# Background
dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=10, ry=10, fill=background_color))

# Title
dwg.add(dwg.text("🔥 My GitHub Stats", insert=(350, 40), fill=text_color,
                 font_size="28px", font_weight="bold", text_anchor="middle"))

# Dividers
dwg.add(dwg.line(start=(233, 60), end=(233, 230), stroke="#444", stroke_width=2))
dwg.add(dwg.line(start=(466, 60), end=(466, 230), stroke="#444", stroke_width=2))

# Total Contributions Panel
dwg.add(dwg.text(str(total_contributions), insert=(116, 110), fill=text_color,
                 font_size="40px", font_weight="bold", text_anchor="middle"))
dwg.add(dwg.text("Total Contributions", insert=(116, 150), fill=text_color,
                 font_size="16px", text_anchor="middle"))
dwg.add(dwg.text(f"{account_created_at.strftime('%b %d, %Y')} - Present",
                 insert=(116, 180), fill=subtext_color, font_size="12px", text_anchor="middle"))

# Current Streak Panel
dwg.add(dwg.circle(center=(350, 110), r=40, stroke=accent_color, stroke_width=5, fill="none"))
dwg.add(dwg.text(str(current_streak), insert=(350, 125), fill=text_color,
                 font_size="40px", font_weight="bold", text_anchor="middle"))
dwg.add(dwg.text("Current Streak", insert=(350, 170), fill=accent_color,
                 font_size="16px", font_weight="bold", text_anchor="middle"))
if current_streak_start and current_streak_end:
    streak_range = f"{current_streak_start.strftime('%b %d')} - {current_streak_end.strftime('%b %d')}"
else:
    streak_range = "No streak"
dwg.add(dwg.text(streak_range, insert=(350, 195), fill=subtext_color,
                 font_size="12px", text_anchor="middle"))

# Longest Streak Panel
dwg.add(dwg.text(str(longest_streak), insert=(584, 110), fill=text_color,
                 font_size="40px", font_weight="bold", text_anchor="middle"))
dwg.add(dwg.text("Longest Streak", insert=(584, 150), fill=text_color,
                 font_size="16px", text_anchor="middle"))
if longest_streak_start and longest_streak_end:
    longest_range = f"{longest_streak_start.strftime('%b %d')} - {longest_streak_end.strftime('%b %d')}"
else:
    longest_range = "N/A"
dwg.add(dwg.text(longest_range, insert=(584, 180), fill=subtext_color,
                 font_size="12px", text_anchor="middle"))

dwg.save()
print("✅ Fancy GitHub Stats SVG updated.")
