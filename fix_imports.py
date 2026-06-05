import sys
with open('frontend/src/components/TicketCard.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.strip() == "import { SeatMap } from './SeatMap';":
        lines.insert(i, "import { Bus, Clock, Star, Bookmark, Wifi, BatteryCharging, Wind } from 'lucide-react';\n")
        break

with open('frontend/src/components/TicketCard.tsx', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("imports fixed")
