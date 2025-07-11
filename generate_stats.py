import requests
import datetime
import svgwrite
import os

# GitHub username and token from secret
USERNAME = "panditpooja"
TOKEN = os.environ["GH_TOKEN"]

headers = {"Authorization": f"Bearer {TOKEN}"}

# GraphQL query for all-time contributions
query = """
{
  user(login: "%s") {
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
      createdAt
    }
  }
}
""" % USERNAME

# Fetch data
response = requests.post(
    "https://api.github.com/graphql",
    json={"query": query},
    headers=headers
)

if response.status_code != 200:
    raise Exception(f"GitHub API Error: {response.status_code} {response.text}")

data = response.json()

# Get total contributions and account creation date
total_contributions = data['data']['user']['contributionsCollection']['totalContributions']
account_created_at = datetime.datetime.strptime(data['data']['user']['createdAt'], "%Y-%m-%dT%H:%M:%SZ").date()

# Process contribution calendar
all_days = []
for week in data['data']['user']['contributionsCollection']['weeks']:
    for day in week['contributionDays']:
        all_days.append({
            "date": datetime.datetime.strptime(day["date"], "%Y-%m-%d").date(),
            "count": day["contributionCount"]
        })

# Calculate streaks
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

# Create SVG
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
