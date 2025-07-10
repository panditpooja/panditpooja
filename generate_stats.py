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

for day in all_days:
    if day["count"] > 0:
        if last_date and (day["date"] - last_date).days == 1:
            temp_streak += 1
        else:
            temp_streak = 1
        if temp_streak > longest_streak:
            longest_streak = temp_streak
        last_date = day["date"]
    else:
        temp_streak = 0

if temp_streak > 0:
    current_streak = temp_streak

# Create SVG
dwg = svgwrite.Drawing("assets/github-stats.svg", size=("600px", "200px"))
dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="#0d1117"))
dwg.add(dwg.text("🔥 GitHub Stats", insert=(20, 40), fill="white", font_size="24px", font_family="Arial"))
dwg.add(dwg.text(f"Total Contributions: {total_contributions}", insert=(20, 80), fill="white", font_size="18px"))
dwg.add(dwg.text(f"Current Streak: {current_streak}", insert=(20, 110), fill="white", font_size="18px"))
dwg.add(dwg.text(f"Longest Streak: {longest_streak}", insert=(20, 140), fill="white", font_size="18px"))
dwg.save()

print("✅ GitHub Stats SVG updated.")
