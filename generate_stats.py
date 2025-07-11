import requests
import datetime
import svgwrite
import os

# GitHub username and token from secret
USERNAME = "panditpooja"
TOKEN = os.environ["GH_TOKEN"]

headers = {"Authorization": f"Bearer {TOKEN}"}

# GraphQL query
query = """
{
  user(login: "%s") {
    contributionsCollection {
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

# Process contribution data
all_days = []
for week in data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']:
    for day in week['contributionDays']:
        all_days.append({
            "date": datetime.datetime.strptime(day["date"], "%Y-%m-%d"),
            "count": day["contributionCount"]
        })

# Calculate stats
total_contributions = sum(day["count"] for day in all_days)
current_streak, longest_streak, temp_streak = 0, 0, 0
last_date = None
start_date, end_date = None, None

for day in all_days:
    if day["count"] > 0:
        if last_date and (day["date"] - last_date).days == 1:
            temp_streak += 1
        else:
            temp_streak = 1
            start_date = day["date"]
        if temp_streak > longest_streak:
            longest_streak = temp_streak
        end_date = day["date"]
        last_date = day["date"]
    else:
        temp_streak = 0

if temp_streak > 0:
    current_streak = temp_streak

# Create fancy SVG
dwg = svgwrite.Drawing("assets/github-stats.svg", size=("600px", "200px"))

# Background panel
dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=15, ry=15, fill="#0d1117", stroke="#333", stroke_width=2))

# Sections divider lines
dwg.add(dwg.line(start=(200, 20), end=(200, 180), stroke="#444", stroke_width=2))
dwg.add(dwg.line(start=(400, 20), end=(400, 180), stroke="#444", stroke_width=2))

# Total Contributions
dwg.add(dwg.text(str(total_contributions), insert=(100, 80), fill="#ffffff", font_size="36px", font_weight="bold", text_anchor="middle"))
dwg.add(dwg.text("Total Contributions", insert=(100, 115), fill="#ffffff", font_size="14px", text_anchor="middle"))
dwg.add(dwg.text(f"{all_days[0]['date'].strftime('%b %d, %Y')} - Present", insert=(100, 145), fill="#999999", font_size="12px", text_anchor="middle"))

# Current Streak
dwg.add(dwg.circle(center=(300, 70), r=35, stroke="#ff9800", stroke_width=5, fill="none"))
dwg.add(dwg.text(str(current_streak), insert=(300, 80), fill="#ffffff", font_size="28px", font_weight="bold", text_anchor="middle"))
dwg.add(dwg.text("Current Streak", insert=(300, 115), fill="#ff9800", font_size="14px", font_weight="bold", text_anchor="middle"))
if start_date and end_date:
    streak_range = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
    dwg.add(dwg.text(streak_range, insert=(300, 145), fill="#999999", font_size="12px", text_anchor="middle"))

# Longest Streak
dwg.add(dwg.text(str(longest_streak), insert=(500, 80), fill="#ffffff", font_size="36px", font_weight="bold", text_anchor="middle"))
dwg.add(dwg.text("Longest Streak", insert=(500, 115), fill="#ffffff", font_size="14px", text_anchor="middle"))
dwg.add(dwg.text(streak_range, insert=(500, 145), fill="#999999", font_size="12px", text_anchor="middle"))

dwg.save()
print("✅ Fancy GitHub Stats SVG updated.")
