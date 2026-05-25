import re
import json
import sys

def parse_mmt_html(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # MMT injects state using self.__next_f.push
    # It contains serialized JSON with lots of escaped quotes
    
    # We can try to extract train objects using regex
    # Looking for patterns like: \"trainName\":\"...\",\"trainNumber\":\"...\"
    
    # Unescape the string a bit to make regex easier
    content = content.replace('\\"', '"')
    
    trains = []
    
    # Regex to find train blocks
    # "trainName":"Cbe Ncj Sf Exp","trainNumber":"22668"
    # "arrivalTime":"00:25","avlClasses":["1A","2A","3A","SL"],"departureTime":"19:30","distance":306,"duration":295
    # Total fare comes from something like "totalFare":180
    
    # Let's extract the big train object list. It starts around "tbsAvailability" or we can just capture the big objects.
    # We can match: "arrivalTime":"(.*?)".*?"departureTime":"(.*?)".*?"duration":(\d+).*?"trainName":"(.*?)","trainNumber":"(.*?)"
    
    pattern = r'"arrivalTime":"([^"]+)".*?"departureTime":"([^"]+)".*?"duration":(\d+).*?"trainName":"([^"]+)","trainNumber":"([^"]+)"'
    
    matches = re.finditer(pattern, content)
    for m in matches:
        arr = m.group(1)
        dep = m.group(2)
        dur_mins = int(m.group(3))
        name = m.group(4)
        num = m.group(5)
        
        # Format duration
        h = dur_mins // 60
        m_dur = dur_mins % 60
        dur_str = f"{h}h {m_dur:02d}m"
        
        # MMT json has totalFare later in the object, maybe we can search near this match for totalFare
        # We can extract a snippet of 2000 chars after the match to find totalFare
        snippet = content[m.end():m.end()+2500]
        fare_match = re.search(r'"totalFare":(\d+)', snippet)
        price = f"₹{fare_match.group(1)}" if fare_match and int(fare_match.group(1)) > 0 else "₹500"
        
        # Avoid duplicates
        if not any(t["number"] == num for t in trains):
            trains.append({
                "train": name,
                "number": num,
                "departure": dep,
                "arrival": arr,
                "duration": dur_str,
                "price": price
            })
        
    print(f"Found {len(trains)} trains.")
    for t in trains:
        print(t)

if __name__ == "__main__":
    parse_mmt_html("debug_mmt.html")
