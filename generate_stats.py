import requests
import datetime
import svgwrite
import os

# -------------------------------
# CONFIGURATION
# -------------------------------
USERNAME = "panditpooja"  # your GitHub username
TOKEN = os.environ.get("GH_TOKEN")  # Token from GitHub Actions secret

if not TOKEN:
    print("❌ ERROR: GH_TOKEN is not set as an environment variable.")
    exit(1)

headers = {"Authorization": f"Bearer {TOKEN}"}

# -------------------------------
# FETCH GITHUB CONTRIBUTIONS
# -------------------------------
query = """
{
  user(login: "%s") {
    createdAt
    contributionsCollection {
      contributionCalendar {
        totalContributions
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
""" % USERNAME

print("📡 Fetching GitHub contribution data...")
response = requests.post(
    "https://api.github.com/graphql",
    json={"query": query},
    headers=headers
)

# -------------------------------
# DEBUGGING API RESPONSE
# -------------------------------
if response.status_code != 200:
    print("❌ GitHub API Error")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    exit(1)

json_response = response.json()
if "errors" in json_response:
    print("❌ GraphQL Error")
    print(json_response["errors"])
    exit(1)

# -------------------------------
# PARSE RESPONSE
# -------------------------------
try:
    user_data = json_response["data"]["user"]
    total_contributions = user_data["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    account_created_at = datetime.datetime.strptime(user_data["createdAt"], "%Y-%m-%dT%H:%M:%SZ").date()
    weeks = user_data["contributionsCollection"]["contributionCalendar"]["weeks"]
except KeyError as e:
    print(f"❌ KeyError: {e}")
    print("Full JSON response:")
    print(json_response)
    exit(1)

# -------------------------------
# CALCULATE STREAKS
# -------------------------------
all_days = []
for week in weeks:
    for day in week["contributionDays"]:
        all_days.append({
            "date": datetime.datetime.strptime(day["date"], "%Y-%m-%d").date(),
            "count": day["contributionCount"]
        })

current_streak, longest_streak, temp_streak = 0, 0, 0
last_date = None
streak_start_date, streak_end_date = None, None

for day in all_days:
    if day["count"] > 0:
        if last_date and (day["date"] - last_date).days == 1:
            temp_streak += 1
        else:
            temp_streak = 1
            streak_start_date = day["date"]
        if temp_streak > longest_streak:
            longest_streak = temp_streak
        streak_end_date = day["date"]
        last_date = day["date"]
    else:
        temp_streak = 0

if temp_streak > 0:
    current_streak = temp_streak

# -------------------------------
# CREATE SVG
# -------------------------------
print("🎨 Generating SVG...")

dwg = svgwrite.Drawing("assets/github-stats.svg", size=("700px", "250px"))

# Background
dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=10, ry=10, fill="#0d1117"))

# Title
dwg.add(dwg.text("🔥 My GitHub Stats", insert=(350, 40), fill="#ffffff",
                 font_size="28px", font_weight="bold", text_anchor="middle"))

# Dividers
dwg.add(dwg.line(start=(233, 60), end=(233, 230), stroke="#444", stroke_width=2))
dwg.add(dwg.line(start=(466, 60), end=(466, 230), stroke="#444", stroke_width=2))

# Total Contributions Panel
dwg.add(dwg.text(str(total_contributions), insert=(116, 110), fill="#ffffff",
                 font_size="40px", font_weight="bold", text_anchor="middle"))
dwg.add(dwg.text("Total Contributions", insert=(116, 150), fill="#ffffff",
                 font_size="16px", text_anchor="middle"))
dwg.add(dwg.text(f"{account_created_at.strftime('%b %d, %Y')} - Present",
                 insert=(116, 180), fill="#999999", font_size="12px", text_anchor="middle"))

# Current Streak Panel
# Circle
dwg.add(dwg.circle(center=(350, 110), r=40, stroke="#ff9800", stroke_width=5, fill="none"))
# Flame Icon
dwg.add(dwg.text("🔥", insert=(338, 100), font_size="20px"))
# Streak Number
dwg.add(dwg.text(str(current_streak), insert=(350, 120), fill="#ffffff",
                 font_size="28px", font_weight="bold", text_anchor="middle"))
# Label
dwg.add(dwg.text("Current Streak", insert=(350, 160), fill="#ff9800",
                 font_size="16px", font_weight="bold", text_anchor="middle"))
# Date range
if streak_start_date and streak_end_date:
    streak_range = f"{streak_start_date.strftime('%b %d')} - {streak_end_date.strftime('%b %d')}"
    dwg.add(dwg.text(streak_range, insert=(350, 190), fill="#999999",
                     font_size="12px", text_anchor="middle"))

# Longest Streak Panel
dwg.add(dwg.text(str(longest_streak), insert=(584, 110), fill="#ffffff",
                 font_size="40px", font_weight="bold", text_anchor="middle"))
dwg.add(dwg.text("Longest Streak", insert=(584, 150), fill="#ffffff",
                 font_size="16px", text_anchor="middle"))
dwg.add(dwg.text(streak_range, insert=(584, 180), fill="#999999",
                 font_size="12px", text_anchor="middle"))

dwg.save()
print("✅ Fancy GitHub Stats SVG updated.")
