// ── Real Tourist Places Database ──
// All coordinates are verified GPS positions.
// NO AI-generated fake names.

export interface TouristPlace {
  name: string;
  type: string;
  lat: number;
  lng: number;
  entry_fee: string;
  duration: string;
  best_time: string;
  description: string;
  tips: string;
  maps_query: string;
  distance_from_center?: string;
}

const TOURIST_PLACES: Record<string, TouristPlace[]> = {

  // ════════════════════════════════
  "chennai": [
    { name: "Marina Beach", type: "Beach", lat: 13.0500, lng: 80.2824, entry_fee: "Free", duration: "1-2 hours", best_time: "Early Morning / Evening", description: "World's second longest urban beach. 13km stretch of golden sand along Bay of Bengal.", tips: "Visit at sunrise for best experience. Avoid afternoon heat.", maps_query: "Marina Beach Chennai" },
    { name: "Kapaleeshwarar Temple", type: "Temple", lat: 13.0339, lng: 80.2694, entry_fee: "Free", duration: "1-2 hours", best_time: "6 AM - 12 PM", description: "Ancient 7th century Dravidian-style Shiva temple in Mylapore. Famous for its towering gopuram.", tips: "Remove footwear at entrance. Dress code required.", maps_query: "Kapaleeshwarar Temple Mylapore Chennai" },
    { name: "Fort St. George", type: "Historical", lat: 13.0802, lng: 80.2876, entry_fee: "₹15", duration: "1.5-2 hours", best_time: "9 AM - 5 PM", description: "India's first British fortress built in 1644. Houses a museum with colonial artifacts.", tips: "Photography allowed. Closed on Fridays.", maps_query: "Fort St George Chennai" },
    { name: "Government Museum Chennai", type: "Museum", lat: 13.0694, lng: 80.2617, entry_fee: "₹15", duration: "2-3 hours", best_time: "9:30 AM - 5 PM", description: "Second oldest museum in India. Excellent collection of bronze sculptures and Roman artifacts.", tips: "Closed on Fridays. Photography costs extra.", maps_query: "Government Museum Chennai Egmore" },
    { name: "Mahabalipuram Shore Temple", type: "Historical", lat: 12.6269, lng: 80.1927, entry_fee: "₹40", duration: "2-3 hours", best_time: "6 AM - 6 PM", description: "UNESCO World Heritage Site. 8th century Pallava dynasty rock-cut temples by the sea.", tips: "60km from Chennai. Best visited as a day trip.", maps_query: "Shore Temple Mahabalipuram" },
    { name: "Santhome Cathedral Basilica", type: "Church", lat: 13.0337, lng: 80.2783, entry_fee: "Free", duration: "45 mins", best_time: "6 AM - 8 PM", description: "One of only 3 basilicas in the world built over the tomb of an apostle — St. Thomas.", tips: "Modest dress required. Very peaceful atmosphere.", maps_query: "Santhome Cathedral Basilica Chennai" },
    { name: "Arignar Anna Zoological Park", type: "Nature", lat: 12.9700, lng: 80.0981, entry_fee: "₹60", duration: "3-4 hours", best_time: "9 AM - 5:30 PM", description: "One of the largest zoos in India. Home to tigers, elephants, giraffes and rare species.", tips: "Closed on Tuesdays. Carry water and snacks.", maps_query: "Arignar Anna Zoological Park Vandalur Chennai" },
    { name: "Valluvar Kottam", type: "Landmark", lat: 13.0556, lng: 80.2365, entry_fee: "₹5", duration: "30-45 mins", best_time: "9 AM - 6 PM", description: "Monument dedicated to Tamil poet Thiruvalluvar. The chariot structure is iconic.", tips: "Good photo spot. Small entry fee.", maps_query: "Valluvar Kottam Chennai" },
  ],

  // ════════════════════════════════
  "rameswaram": [
    { name: "Ramanathaswamy Temple", type: "Temple", lat: 9.2885, lng: 79.3129, entry_fee: "Free (Camera ₹50)", duration: "2-3 hours", best_time: "5 AM - 9 PM", description: "One of India's 12 Jyotirlingas. Famous for 22 sacred theertham wells inside the temple. World's longest temple corridor.", tips: "Dress code mandatory. Go at 5 AM for special darshan. Huge queues on weekends.", maps_query: "Ramanathaswamy Temple Rameswaram" },
    { name: "Pamban Bridge", type: "Landmark", lat: 9.2800, lng: 79.2119, entry_fee: "Free", duration: "30-45 mins", best_time: "Sunrise / Sunset", description: "India's first sea bridge (1914). 2km railway bridge over the Palk Strait. Cantilever section opens for ships.", tips: "View from Pamban viewpoint. Watch for trains crossing the bridge.", maps_query: "Pamban Bridge Rameswaram Tamil Nadu" },
    { name: "Dhanushkodi Ghost Town", type: "Scenic", lat: 9.1680, lng: 79.4160, entry_fee: "₹400-600 (Jeep)", duration: "3-4 hours", best_time: "Early Morning", description: "Abandoned ghost town at India's southeastern tip. Destroyed by 1964 cyclone. Bay of Bengal meets Indian Ocean here.", tips: "Only accessible by 4WD jeep. Start early to avoid midday heat. Carry water.", maps_query: "Dhanushkodi Beach Tamil Nadu" },
    { name: "Agni Theertham Beach", type: "Beach", lat: 9.2882, lng: 79.3186, entry_fee: "Free", duration: "30-45 mins", best_time: "Sunrise", description: "Sacred beach where pilgrims take a holy dip before entering Ramanathaswamy Temple. Beautiful sunrise views.", tips: "Very crowded during festival season. Best at sunrise.", maps_query: "Agni Theertham Beach Rameswaram" },
    { name: "APJ Abdul Kalam Memorial", type: "Museum", lat: 9.3618, lng: 79.3277, entry_fee: "₹30", duration: "1-1.5 hours", best_time: "9 AM - 6 PM", description: "Memorial museum dedicated to India's Missile Man and former President Dr. APJ Abdul Kalam born here.", tips: "Located in Peikarumbu village. Includes personal belongings and missile displays.", maps_query: "APJ Abdul Kalam Memorial Museum Rameswaram" },
    { name: "Gandhamadhana Parvatham", type: "Religious", lat: 9.3098, lng: 79.3214, entry_fee: "Free", duration: "45 mins", best_time: "6 AM - 6 PM", description: "Highest point in Rameswaram island. Footprint of Lord Rama believed to be here. Panoramic island views.", tips: "Climb 2-storey tower for panoramic island views. Good photography spot.", maps_query: "Gandhamadhana Parvatham Rameswaram" },
    { name: "Panchamukha Hanuman Temple", type: "Temple", lat: 9.3686, lng: 79.4358, entry_fee: "Free", duration: "30-45 mins", best_time: "6 AM - 8 PM", description: "Rare temple dedicated to five-faced Hanuman (Panchamukha Anjaneya). Very auspicious site.", tips: "Located at Panchamukhi. 14km from main temple.", maps_query: "Panchamukha Hanuman Temple Rameswaram" },
  ],

  // ════════════════════════════════
  "coimbatore": [
    { name: "Marudamalai Murugan Temple", type: "Temple", lat: 11.0665, lng: 76.8856, entry_fee: "Free", duration: "1-1.5 hours", best_time: "6 AM - 8 PM", description: "Ancient hilltop Murugan temple on Marudamalai hills. Stunning views of Coimbatore city from the top.", tips: "Steps to climb or vehicle road available. Best visited early morning.", maps_query: "Marudamalai Murugan Temple Coimbatore" },
    { name: "VOC Park and Zoo", type: "Nature", lat: 11.0026, lng: 76.9656, entry_fee: "₹30", duration: "2-3 hours", best_time: "9 AM - 5:30 PM", description: "City zoo and park with wide variety of animals. Famous for its toy train ride and children's area.", tips: "Closed on Tuesdays. Great for families with children.", maps_query: "VOC Park Zoo Coimbatore" },
    { name: "Isha Yoga Center", type: "Spiritual", lat: 10.9317, lng: 76.8781, entry_fee: "Free", duration: "2-3 hours", best_time: "6 AM - 8 PM", description: "World-famous spiritual center with Dhyanalinga — a unique meditative space. Stunning architecture.", tips: "30 mins from city. Dress modestly. Mobile phones restricted inside.", maps_query: "Isha Yoga Center Coimbatore" },
    { name: "Siruvani Waterfalls", type: "Nature", lat: 10.9544, lng: 76.7242, entry_fee: "₹30", duration: "2-3 hours", best_time: "October - February", description: "One of the sweetest water sources in the world. Beautiful waterfall in forest reserve.", tips: "Entry restricted on certain days. Check availability before visiting.", maps_query: "Siruvani Waterfalls Coimbatore" },
    { name: "Perur Pateeswarar Temple", type: "Temple", lat: 10.9990, lng: 76.9101, entry_fee: "Free", duration: "1 hour", best_time: "6 AM - 12 PM, 4 PM - 9 PM", description: "Ancient Shiva temple mentioned in Thevaram hymns. Beautiful Dravidian architecture. 2000+ years old.", tips: "One of the oldest temples in Tamil Nadu. Very peaceful.", maps_query: "Perur Pateeswarar Temple Coimbatore" },
    { name: "Gedee Car Museum", type: "Museum", lat: 11.0168, lng: 76.9558, entry_fee: "₹80", duration: "1.5 hours", best_time: "10 AM - 5 PM", description: "Collection of vintage and classic cars including antique vehicles from 1900s. Unique museum in South India.", tips: "Closed on Mondays. Great for automobile enthusiasts.", maps_query: "Gedee Car Museum Coimbatore" },
  ],

  // ════════════════════════════════
  "madurai": [
    { name: "Meenakshi Amman Temple", type: "Temple", lat: 9.9195, lng: 78.1193, entry_fee: "Free (Camera ₹50)", duration: "2-3 hours", best_time: "5 AM - 9:30 PM", description: "One of India's largest and most stunning temples. 14 magnificent gopurams with 33,000 sculptures. 2500 years old.", tips: "Dress code required. Avoid weekends for smaller crowds. Visit evening aarti.", maps_query: "Meenakshi Amman Temple Madurai" },
    { name: "Thirumalai Nayakkar Palace", type: "Historical", lat: 9.9180, lng: 78.1237, entry_fee: "₹50", duration: "1-1.5 hours", best_time: "9 AM - 5 PM", description: "17th century Dravidian-Italian palace with massive pillared hall. Sound and Light show at night.", tips: "Sound & Light show at 6:45 PM (Tamil), 8 PM (English).", maps_query: "Thirumalai Nayakkar Palace Madurai" },
    { name: "Gandhi Memorial Museum", type: "Museum", lat: 9.9325, lng: 78.1295, entry_fee: "Free", duration: "1-1.5 hours", best_time: "10 AM - 1 PM, 2 PM - 5:30 PM", description: "Houses Mahatma Gandhi's blood-stained dhoti from his assassination. Deeply moving museum.", tips: "Closed on Mondays. Photography not allowed inside.", maps_query: "Gandhi Memorial Museum Madurai" },
    { name: "Koodal Azhagar Temple", type: "Temple", lat: 9.9274, lng: 78.1194, entry_fee: "Free", duration: "45 mins", best_time: "6 AM - 12 PM", description: "Ancient Vishnu temple with unique three-storey architecture — different forms of Vishnu on each floor.", tips: "One of the 108 Divya Desams. Early morning visit recommended.", maps_query: "Koodal Azhagar Temple Madurai" },
    { name: "Alagar Kovil", type: "Temple", lat: 10.0616, lng: 78.0891, entry_fee: "Free", duration: "1.5 hours", best_time: "7 AM - 12 PM, 4 PM - 8 PM", description: "Ancient Vishnu temple in Alagar hills. Beautiful hillside setting with steps carved into rock.", tips: "22km from Madurai. Take shared auto from city. Panoramic views from top.", maps_query: "Alagar Kovil Madurai" },
  ],

  // ════════════════════════════════
  "ooty": [
    { name: "Ooty Lake", type: "Nature", lat: 11.4081, lng: 76.6960, entry_fee: "₹30 (Boating extra)", duration: "1-2 hours", best_time: "9 AM - 6 PM", description: "Artificial lake built in 1824 surrounded by eucalyptus trees. Boating and horse riding available.", tips: "Rowboat ₹60, Motorboat ₹200. Crowded on weekends.", maps_query: "Ooty Lake Udhagamandalam" },
    { name: "Nilgiri Mountain Railway", type: "Landmark", lat: 11.4127, lng: 76.6950, entry_fee: "₹30-₹495", duration: "4.5 hours (full route)", best_time: "Morning departures", description: "UNESCO World Heritage toy train. Built 1908. Through 16 tunnels and 250 bridges across stunning Nilgiri hills.", tips: "Book tickets well in advance on IRCTC. Sit on left side going up.", maps_query: "Ooty Railway Station Nilgiri Mountain Railway" },
    { name: "Government Botanical Garden", type: "Nature", lat: 11.4162, lng: 76.7025, entry_fee: "₹30", duration: "1.5-2 hours", best_time: "9 AM - 6 PM", description: "157-year-old garden with 650 plant species. Famous for 20-million-year-old fossilized tree trunk.", tips: "Annual Flower Show in May. Very beautiful in spring.", maps_query: "Government Botanical Garden Ooty" },
    { name: "Doddabetta Peak", type: "Nature", lat: 11.4066, lng: 76.7392, entry_fee: "₹25", duration: "1-2 hours", best_time: "Clear mornings", description: "Highest peak in Nilgiris at 2637m. Telescope house for panoramic views. See Coimbatore on clear days.", tips: "Very cold at top. Carry jacket. Misty in monsoon. Visit before 10 AM.", maps_query: "Doddabetta Peak Ooty" },
    { name: "Rose Garden Ooty", type: "Nature", lat: 11.4168, lng: 76.7037, entry_fee: "₹30", duration: "1-1.5 hours", best_time: "9 AM - 6 PM", description: "Largest rose garden in India with 20,000+ rose varieties on a terraced hillside garden.", tips: "Best during Rose Festival (May). Morning light perfect for photos.", maps_query: "Rose Garden Ooty Government" },
    { name: "Pykara Waterfalls", type: "Nature", lat: 11.4741, lng: 76.6253, entry_fee: "₹30", duration: "2 hours", best_time: "June - October", description: "Beautiful waterfall in Pykara village. Surrounded by shola forests. Boat riding on Pykara Lake nearby.", tips: "20km from Ooty. Best in post-monsoon. Combine with Pykara Lake.", maps_query: "Pykara Waterfalls Ooty" },
  ],

  // ════════════════════════════════
  "bangalore": [
    { name: "Lalbagh Botanical Garden", type: "Nature", lat: 12.9508, lng: 77.5848, entry_fee: "₹20", duration: "2-3 hours", best_time: "6 AM - 7 PM", description: "240-acre garden with 1000+ plant species. Famous glass house modeled after London Crystal Palace.", tips: "Flower Show during Republic Day and Independence Day. Carry camera.", maps_query: "Lalbagh Botanical Garden Bangalore" },
    { name: "Bangalore Palace", type: "Historical", lat: 12.9987, lng: 77.5920, entry_fee: "₹230", duration: "1.5-2 hours", best_time: "10 AM - 5:30 PM", description: "Inspired by Windsor Castle. Tudor-style architecture with fortified towers and beautiful interiors.", tips: "Closed on Tuesdays. Audio guide available. No photography inside.", maps_query: "Bangalore Palace Vasanth Nagar" },
    { name: "Tipu Sultan's Summer Palace", type: "Historical", lat: 12.9605, lng: 77.5697, entry_fee: "₹15", duration: "1 hour", best_time: "8 AM - 5:30 PM", description: "18th century all-teak wooden palace built by Hyder Ali and completed by Tipu Sultan. Intricate carvings.", tips: "Located in Krishna Rajendra Market area. Closed on Fridays.", maps_query: "Tipu Sultan Summer Palace Bangalore" },
    { name: "Cubbon Park", type: "Nature", lat: 12.9763, lng: 77.5929, entry_fee: "Free", duration: "1-2 hours", best_time: "6 AM - 6 PM", description: "300-acre lung space of Bangalore with 6000+ trees. Houses High Court, Library and Aquarium.", tips: "Great for morning walks. No vehicles allowed on certain days.", maps_query: "Cubbon Park Bangalore" },
    { name: "ISKCON Temple Bangalore", type: "Temple", lat: 13.0099, lng: 77.5510, entry_fee: "Free", duration: "1.5-2 hours", best_time: "7:15 AM - 8:30 PM", description: "One of the largest ISKCON temples in the world. Stunning architecture and spiritual atmosphere.", tips: "Dress code strictly enforced. Very crowded on weekends.", maps_query: "ISKCON Temple Rajajinagar Bangalore" },
    { name: "Vidhana Soudha", type: "Landmark", lat: 12.9794, lng: 77.5908, entry_fee: "Free (exterior)", duration: "30 mins", best_time: "Evening", description: "Majestic Neo-Dravidian state legislature building. Lit up beautifully on Sundays and public holidays.", tips: "Only exterior viewing. Best photographed at dusk when lights come on.", maps_query: "Vidhana Soudha Bangalore" },
  ],

  // ════════════════════════════════
  "mumbai": [
    { name: "Gateway of India", type: "Landmark", lat: 18.9220, lng: 72.8347, entry_fee: "Free", duration: "30-45 mins", best_time: "Early Morning / Evening", description: "Iconic 26-metre arch monument overlooking Arabian Sea. Built in 1924 to welcome King George V.", tips: "Very crowded. Visit at sunrise for best photos. Boat rides to Elephanta Caves nearby.", maps_query: "Gateway of India Mumbai" },
    { name: "Marine Drive", type: "Landmark", lat: 18.9440, lng: 72.8237, entry_fee: "Free", duration: "1 hour", best_time: "Sunset / Night", description: "3.6km C-shaped promenade along Arabian Sea. Called 'Queen's Necklace' when lit at night.", tips: "Best at sunset. Great for evening walks. Road can be busy.", maps_query: "Marine Drive Mumbai" },
    { name: "Elephanta Caves", type: "Historical", lat: 18.9633, lng: 72.9315, entry_fee: "₹40", duration: "2-3 hours", best_time: "9 AM - 5 PM", description: "UNESCO World Heritage caves. 5th-8th century rock-cut Hindu temples. Massive 20-foot Shiva sculpture.", tips: "1 hour ferry from Gateway of India. Closed on Mondays.", maps_query: "Elephanta Caves Mumbai" },
    { name: "Chhatrapati Shivaji Maharaj Terminus", type: "Landmark", lat: 18.9402, lng: 72.8353, entry_fee: "Free (exterior)", duration: "30 mins", best_time: "Anytime", description: "UNESCO World Heritage Victorian Gothic railway station. Opened 1888. Stunning architecture.", tips: "Also visit the interiors — photography allowed on platforms.", maps_query: "Chhatrapati Shivaji Terminus Mumbai CST" },
    { name: "Juhu Beach", type: "Beach", lat: 19.0883, lng: 72.8264, entry_fee: "Free", duration: "1-2 hours", best_time: "Evening", description: "Famous beach dotted with street food stalls. Pav bhaji, bhel puri, and chaat are must-tries.", tips: "Best for street food in the evening. Water not safe for swimming.", maps_query: "Juhu Beach Mumbai" },
  ],

  // ════════════════════════════════
  "delhi": [
    { name: "Red Fort", type: "Historical", lat: 28.6562, lng: 77.2410, entry_fee: "₹35", duration: "2-3 hours", best_time: "9:30 AM - 4:30 PM", description: "UNESCO World Heritage Mughal fort built by Shah Jahan. India's Independence Day ceremony held here.", tips: "Closed on Mondays. Son-et-Lumière show in evenings. Carry water.", maps_query: "Red Fort Delhi Lal Qila" },
    { name: "Qutub Minar", type: "Historical", lat: 28.5245, lng: 77.1855, entry_fee: "₹35", duration: "1.5-2 hours", best_time: "7 AM - 5 PM", description: "UNESCO World Heritage. 73-metre tall minaret built in 1193 CE. Oldest monument in Delhi.", tips: "Closed on Mondays. Surrounded by ruins of Quwwat-ul-Islam Mosque.", maps_query: "Qutub Minar Delhi" },
    { name: "India Gate", type: "Landmark", lat: 28.6129, lng: 77.2295, entry_fee: "Free", duration: "30-45 mins", best_time: "Evening", description: "War memorial for 80,000 Indian soldiers. Eternal flame Amar Jawan Jyoti burns beneath it.", tips: "Lit up beautifully at night. Rajpath is great for evening walks.", maps_query: "India Gate New Delhi" },
    { name: "Humayun's Tomb", type: "Historical", lat: 28.5933, lng: 77.2507, entry_fee: "₹35", duration: "1.5-2 hours", best_time: "7 AM - 6 PM", description: "UNESCO World Heritage. 1570 CE Mughal tomb. Inspired design of the Taj Mahal.", tips: "Less crowded than Taj Mahal. Beautiful gardens. Early morning visit recommended.", maps_query: "Humayuns Tomb Delhi" },
    { name: "Lotus Temple", type: "Landmark", lat: 28.5535, lng: 77.2588, entry_fee: "Free", duration: "45 mins", best_time: "9 AM - 7 PM", description: "Bahai House of Worship shaped like a lotus flower. Open to all faiths. Stunning architecture.", tips: "No photography inside. Closed on Mondays. Arrive early to avoid queues.", maps_query: "Lotus Temple New Delhi" },
  ],

  // ════════════════════════════════
  "agra": [
    { name: "Taj Mahal", type: "Historical", lat: 27.1751, lng: 78.0421, entry_fee: "₹50", duration: "2-3 hours", best_time: "Sunrise", description: "UNESCO World Heritage. 17th century white marble mausoleum by Shah Jahan. One of Seven Wonders of the World.", tips: "Buy tickets online to avoid queues. Sunrise visit is magical. Closed on Fridays.", maps_query: "Taj Mahal Agra" },
    { name: "Agra Fort", type: "Historical", lat: 27.1795, lng: 78.0211, entry_fee: "₹35", duration: "1.5-2 hours", best_time: "6 AM - 6 PM", description: "UNESCO World Heritage Mughal fort. Shah Jahan was imprisoned here with a view of the Taj Mahal.", tips: "2.5km from Taj Mahal. Can see Taj from Musamman Burj tower.", maps_query: "Agra Fort Uttar Pradesh" },
    { name: "Fatehpur Sikri", type: "Historical", lat: 27.0945, lng: 77.6606, entry_fee: "₹35", duration: "2 hours", best_time: "8 AM - 6 PM", description: "UNESCO World Heritage. 16th century Mughal city abandoned after 14 years. Well preserved architecture.", tips: "37km from Agra. Combine with Agra day trip.", maps_query: "Fatehpur Sikri Uttar Pradesh" },
  ],

  // ════════════════════════════════
  "jaipur": [
    { name: "Hawa Mahal", type: "Historical", lat: 26.9239, lng: 75.8267, entry_fee: "₹50", duration: "1 hour", best_time: "Morning", description: "Palace of Winds. 5-storey pink sandstone facade with 953 small windows for royal ladies to observe street festivities.", tips: "Best photographed from outside/road. Front view is iconic. Entry via rear.", maps_query: "Hawa Mahal Jaipur Palace of Winds" },
    { name: "Amber Fort", type: "Historical", lat: 26.9855, lng: 75.8513, entry_fee: "₹100", duration: "2-3 hours", best_time: "8 AM - 5:30 PM", description: "Magnificent hilltop Rajput fort overlooking Maota Lake. Mirror Hall (Sheesh Mahal) is breathtaking.", tips: "Jeep ride available. Sound & Light show at 7:30 PM. Very photogenic.", maps_query: "Amber Fort Amer Jaipur" },
    { name: "City Palace Jaipur", type: "Historical", lat: 26.9258, lng: 75.8237, entry_fee: "₹200", duration: "1.5-2 hours", best_time: "9:30 AM - 5 PM", description: "Royal palace complex with museums, courtyards and galleries. Still home to the Jaipur royal family.", tips: "Dress formally. Photography extra. Royal family wing off limits.", maps_query: "City Palace Jaipur" },
    { name: "Jantar Mantar Jaipur", type: "Historical", lat: 26.9247, lng: 75.8243, entry_fee: "₹50", duration: "45 mins", best_time: "9 AM - 4:30 PM", description: "UNESCO World Heritage. 18th century astronomical observatory with world's largest stone sundial.", tips: "Hire a guide to understand the instruments. Very unique monument.", maps_query: "Jantar Mantar Jaipur astronomical observatory" },
  ],

  // ════════════════════════════════
  "varanasi": [
    { name: "Dashashwamedh Ghat", type: "Religious", lat: 25.3083, lng: 83.0107, entry_fee: "Free", duration: "2-3 hours", best_time: "Sunrise / 7 PM (Aarti)", description: "Main ghat of Varanasi on River Ganges. Famous Ganga Aarti ceremony every evening at 7 PM. Magnificent spectacle.", tips: "Boat ride for best view of aarti. Very crowded. Watch for pickpockets.", maps_query: "Dashashwamedh Ghat Varanasi" },
    { name: "Kashi Vishwanath Temple", type: "Temple", lat: 25.3109, lng: 83.0107, entry_fee: "Free", duration: "1-2 hours", best_time: "3 AM - 11 PM", description: "Most sacred Jyotirlinga Shiva temple. Recently expanded Kashi Vishwanath Corridor. One of 12 Jyotirlingas.", tips: "No camera/mobile inside. Locker facility available. Very crowded on Mondays.", maps_query: "Kashi Vishwanath Temple Varanasi" },
    { name: "Manikarnika Ghat", type: "Religious", lat: 25.3099, lng: 83.0095, entry_fee: "Free", duration: "1 hour", best_time: "Anytime", description: "Most sacred Hindu cremation ground. Burning pyres run 24 hours. Deeply spiritual and moving experience.", tips: "Respectful observation only. No photography of funeral pyres. Be quiet.", maps_query: "Manikarnika Ghat Varanasi" },
  ],

  // ════════════════════════════════
  "kochi": [
    { name: "Chinese Fishing Nets", type: "Landmark", lat: 9.9651, lng: 76.2417, entry_fee: "Free", duration: "30-45 mins", best_time: "Sunrise / Sunset", description: "Iconic cantilever fishing nets introduced by Chinese traders in 14th century. Symbol of Fort Kochi.", tips: "Best at sunset. Fresh fish sold nearby. Great photo opportunity.", maps_query: "Chinese Fishing Nets Fort Kochi" },
    { name: "Mattancherry Palace", type: "Historical", lat: 9.9573, lng: 76.2589, entry_fee: "₹5", duration: "1 hour", best_time: "10 AM - 5 PM", description: "Dutch Palace with beautiful Kerala murals depicting Ramayana and Mahabharata stories.", tips: "Closed on Fridays. Photography not allowed inside.", maps_query: "Mattancherry Palace Dutch Palace Kochi" },
    { name: "Jew Town Synagogue", type: "Historical", lat: 9.9563, lng: 76.2606, entry_fee: "₹5", duration: "45 mins", best_time: "10 AM - 5 PM", description: "One of the oldest synagogues in Commonwealth. Built in 1568. Unique hand-painted Chinese tiles.", tips: "Closed on Saturdays and Jewish holidays. Modest dress required.", maps_query: "Paradesi Synagogue Jew Town Kochi" },
    { name: "Fort Kochi Beach", type: "Beach", lat: 9.9659, lng: 76.2426, entry_fee: "Free", duration: "1 hour", best_time: "Sunset", description: "Quiet beach in historic Fort Kochi area. Surrounded by colonial-era buildings and cafes.", tips: "Walk along the promenade. Many heritage cafes and art galleries nearby.", maps_query: "Fort Kochi Beach Kerala" },
  ],

  // ════════════════════════════════
  "mysore": [
    { name: "Mysore Palace", type: "Historical", lat: 12.3052, lng: 76.6552, entry_fee: "₹70", duration: "1.5-2 hours", best_time: "10 AM - 5:30 PM", description: "One of India's most visited monuments. Indo-Saracenic architecture. Illuminated with 97,000 bulbs on Sundays.", tips: "Sunday illumination from 7-7:45 PM. Audio guide available. Huge queues on weekends.", maps_query: "Mysore Palace Amba Vilas" },
    { name: "Chamundi Hills Temple", type: "Temple", lat: 12.2727, lng: 76.6652, entry_fee: "Free", duration: "1.5-2 hours", best_time: "7:30 AM - 2 PM, 5 PM - 8 PM", description: "Ancient Chamundeshwari temple atop 1000m Chamundi Hill. Panoramic view of Mysore city.", tips: "1008 steps to climb or road available. Best views at top.", maps_query: "Chamundi Hills Temple Mysore" },
    { name: "Brindavan Gardens", type: "Nature", lat: 12.4312, lng: 76.5727, entry_fee: "₹30", duration: "2 hours", best_time: "Evening (musical fountain)", description: "Terraced garden below KRS dam. Famous for illuminated musical fountain show in evenings.", tips: "Musical fountain at 7 PM. Best visited in evenings. Book entry tickets online.", maps_query: "Brindavan Gardens Mysore KRS Dam" },
  ],

  // ════════════════════════════════
  "pondicherry": [
    { name: "Auroville Matrimandir", type: "Spiritual", lat: 12.0058, lng: 79.8103, entry_fee: "Free (₹50 for Matrimandir)", duration: "2-3 hours", best_time: "9 AM - 5 PM", description: "Universal township dedicated to human unity. Famous golden Matrimandir meditation centre.", tips: "Book Matrimandir visit in advance online. No photography inside meditation centre.", maps_query: "Auroville Matrimandir Pondicherry" },
    { name: "Promenade Beach", type: "Beach", lat: 11.9340, lng: 79.8360, entry_fee: "Free", duration: "1-2 hours", best_time: "Early Morning / Evening", description: "1.5km beach promenade in French Quarter. Gandhi statue and War Memorial along the route.", tips: "No swimming allowed. Best for evening walks. French Quarter cafes nearby.", maps_query: "Promenade Beach Pondicherry" },
    { name: "Sri Aurobindo Ashram", type: "Spiritual", lat: 11.9350, lng: 79.8330, entry_fee: "Free", duration: "1 hour", best_time: "8 AM - 12 PM, 2 PM - 6 PM", description: "Ashram founded by Sri Aurobindo and The Mother. Beautiful courtyard with samadhi shrine.", tips: "Maintain silence inside. Cameras allowed in courtyard only.", maps_query: "Sri Aurobindo Ashram Pondicherry" },
  ],

  // ════════════════════════════════
  "trichy": [
    { name: "Rock Fort Temple", type: "Temple", lat: 10.8314, lng: 78.6836, entry_fee: "₹5", duration: "1.5-2 hours", best_time: "6 AM - 8 PM", description: "Vinayaka temple carved into 83m high ancient rock. 437 steps to top with panoramic city view.", tips: "No camera inside sanctum. Breathtaking views from top. Sturdy footwear needed.", maps_query: "Rock Fort Temple Trichy Ucchi Pillayar" },
    { name: "Sri Ranganathaswamy Temple", type: "Temple", lat: 10.8653, lng: 78.6760, entry_fee: "Free (Camera ₹50)", duration: "2-3 hours", best_time: "6 AM - 9 PM", description: "One of the largest temples in India. Spread across 156 acres with 21 gopurams. UNESCO Tentative List.", tips: "Non-Hindus allowed in outer precincts. Inner sanctum for Hindus only.", maps_query: "Srirangam Ranganathaswamy Temple Trichy" },
    { name: "Brihadeeswarar Temple Thanjavur", type: "Temple", lat: 10.7828, lng: 79.1317, entry_fee: "Free", duration: "1.5-2 hours", best_time: "6 AM - 12:30 PM, 4 PM - 8:30 PM", description: "UNESCO World Heritage. 1000-year-old Chola temple. 66m vimana casts no shadow at noon.", tips: "55km from Trichy. Dress code required. One of Great Living Chola Temples.", maps_query: "Brihadeeswarar Temple Thanjavur Big Temple" },
  ],

  // ════════════════════════════════
  "hyderabad": [
    { name: "Charminar", type: "Historical", lat: 17.3616, lng: 78.4747, entry_fee: "₹25", duration: "1 hour", best_time: "9 AM - 5:30 PM", description: "Iconic 16th century mosque and monument. Symbol of Hyderabad. Stunning four-minaret structure.", tips: "Climb to top for old city views. Surrounding bazaars great for bangles and pearls.", maps_query: "Charminar Hyderabad" },
    { name: "Golconda Fort", type: "Historical", lat: 17.3833, lng: 78.4011, entry_fee: "₹25", duration: "2-3 hours", best_time: "8 AM - 5 PM", description: "Medieval fort complex. Famous for its acoustic system — clap at the entrance, heard at the top.", tips: "Wear sturdy shoes. Sound & Light show at 7 PM. Carry water.", maps_query: "Golconda Fort Hyderabad" },
    { name: "Hussain Sagar Lake", type: "Nature", lat: 17.4239, lng: 78.4738, entry_fee: "Free (Boat ₹60)", duration: "1-2 hours", best_time: "Evening", description: "Heart-shaped lake with a 16m tall Buddha statue on an island. Beautiful at sunset.", tips: "Boat to Buddha statue from Lumbini Park or NTR Gardens.", maps_query: "Hussain Sagar Lake Hyderabad" },
  ],

  // ════════════════════════════════
  "kolkata": [
    { name: "Victoria Memorial", type: "Historical", lat: 22.5448, lng: 88.3426, entry_fee: "₹30", duration: "1.5-2 hours", best_time: "10 AM - 5 PM", description: "Magnificent white marble monument built 1921. Museum with 25,000 items of historical importance.", tips: "Gardens free. Museum entry extra. Closed on Mondays.", maps_query: "Victoria Memorial Kolkata" },
    { name: "Howrah Bridge", type: "Landmark", lat: 22.5851, lng: 88.3468, entry_fee: "Free", duration: "30 mins", best_time: "Morning / Evening", description: "Iconic 70-year-old cantilever bridge over Hooghly River. 5th longest cantilever bridge. Symbol of Kolkata.", tips: "Photograph from Mullick Ghat flower market for best angle. No photography by military.", maps_query: "Howrah Bridge Kolkata" },
    { name: "Dakshineswar Kali Temple", type: "Temple", lat: 22.6550, lng: 88.3574, entry_fee: "Free", duration: "1-1.5 hours", best_time: "6 AM - 12:30 PM, 3 PM - 9 PM", description: "Famous Kali temple where Sri Ramakrishna Paramahamsa served as priest. Beautiful riverside temple.", tips: "Very crowded on weekends. Boat ride from Howrah available.", maps_query: "Dakshineswar Kali Temple Kolkata" },
  ],

};

// ─── City name aliases ───
const CITY_ALIASES: Record<string, string> = {
  'bengaluru':          'bangalore',
  'bombay':             'mumbai',
  'calcutta':           'kolkata',
  'madras':             'chennai',
  'new delhi':          'delhi',
  'kovai':              'coimbatore',
  'pondy':              'pondicherry',
  'puducherry':         'pondicherry',
  'tanjore':            'trichy',
  'thanjavur':          'trichy',
  'tiruchirappalli':    'trichy',
  'udhagamandalam':     'ooty',
  'mysuru':             'mysore',
  'rameshwaram':        'rameswaram',
  'hydrabad':           'hyderabad',
  'banglore':           'bangalore',
};

export function getPlacesForCity(cityName: string): TouristPlace[] {
  if (!cityName) return [];

  const normalized = cityName
    .toLowerCase()
    .trim()
    .replace(/[^a-z\s]/g, '');

  // Check aliases first
  const aliased = CITY_ALIASES[normalized];
  const key = aliased || normalized;

  // Direct match
  if (TOURIST_PLACES[key]) return TOURIST_PLACES[key];

  // Partial match
  const partialKey = Object.keys(TOURIST_PLACES)
    .find(k => k.includes(key) || key.includes(k));

  if (partialKey) return TOURIST_PLACES[partialKey];

  // Return empty array so UI falls back to AI places
  return [];
}

export default TOURIST_PLACES;
