# 1️⃣ ส่วน Import Library
import folium
import streamlit as st
import random
import heapq
import json
import time
import streamlit.components.v1 as components
import math
# from backend.cbs_algorithm import *

from geopy.distance import geodesic 
# from cbs import *    # ในที่นี้เราจะนิยามฟังก์ชัน CBS ภายในโค้ดเลย




def a_star_search(graph, start, goal):
    """A* algorithm สำหรับหาเส้นทางจาก start ไป goal"""
    open_set = [(0, start)]  # (cost, node)
    came_from = {}
    g_score = {node: float('inf') for node in graph}
    g_score[start] = 0
    f_score = {node: float('inf') for node in graph}
    f_score[start] = heuristic(start, goal)

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            return path[::-1]

        for neighbor in graph[current]:
            tentative_g_score = g_score[current] + graph[current][neighbor]
            if tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return []  # หากหาเส้นทางไม่ได้

#! สิ่งที่ทำเพิ่ม
# - คำนวณระยะทางจริง
# - กำหนดความเร็วเดินคงที่
# - แบ่ง time step ตามเวลาที่ใช้เดินจริง

def interpolate_position(start, end, fraction):
    """คำนวณตำแหน่งระหว่าง start กับ end ตาม fraction (0-1)
       คืนค่าเป็น [lat, lon]"""
    return [
        start[0] + (end[0] - start[0]) * fraction,
        start[1] + (end[1] - start[1]) * fraction
    ]

def add_temporary_node(graph, point):
    # หาก point ไม่อยู่ใน graph ให้หา node ใกล้เคียงที่สุดใน graph
    if point in graph:
        return graph
    # คัดลอก graph เดิม (หรือสร้าง graph ชั่วคราวใหม่)
    temp_graph = {node: neighbors.copy() for node, neighbors in graph.items()}
    # หา node ใกล้เคียงที่สุด
    nearest = min(graph.keys(), key=lambda node: geodesic(point, node).meters)
    # เพิ่ม point เป็น node ใหม่ เชื่อมต่อกับ nearest
    temp_graph[point] = {nearest: geodesic(point, nearest).meters}
    # สำหรับ node nearest ให้เพิ่มการเชื่อมต่อกลับไปยัง point
    temp_graph[nearest][point] = geodesic(point, nearest).meters
    return temp_graph


def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    return path[::-1]

# 2️⃣ ฟังก์ชันช่วยสำหรับ A* Search (low-level search)
def heuristic(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def a_star_search(graph, start, goal):
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {node: float('inf') for node in graph}
    g_score[start] = 0
    f_score = {node: float('inf') for node in graph}
    f_score[start] = heuristic(start, goal)

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            return reconstruct_path(came_from, current)
        for neighbor, cost in graph[current].items():
            tentative_g_score = g_score[current] + cost
            if tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return []

# -----------------------------------------------------------------------------
# ฟังก์ชันใหม่สำหรับคำนวณ timeline ของ agent โดยใช้ระยะทางจริง
def compute_segment_boundaries(path, t_per_meter, simulation_time_step):
    """
    - ฟังก์ชันนี้ใช้คำนวณจุดแบ่งเวลา (time boundaries) สำหรับแต่ละส่วน (segment) ของเส้นทาง 
    - แปลงระยะทางจริงให้เป็นจำนวน time steps ในการจำลอง
    """

    """
    path: เส้นทางที่เป็นชุดของพิกัด
    t_per_meter: เวลาที่ใช้ต่อระยะทาง 1 เมตร
    simulation_time_step: ขนาดของ time step ในการจำลอง
    """
    # t_per_meter = 0.1           # เวลาที่ใช้เดิน 1 เมตร (วินาที)
    # simulation_time_step = 1    # 1 วินาทีต่อ time step

    boundaries = [0]
    total_steps = 0
    for i in range(len(path)-1):
        d = geodesic(path[i], path[i+1]).meters #  สำหรับแต่ละ segment คำนวณระยะทางจริงระหว่างจุดด้วย geodesic().meters
        
        seg_time = d * t_per_meter # คำนวณเวลาที่ใช้สำหรับ segment นั้น

        seg_steps = max(1, int(round(seg_time / simulation_time_step))) # แปลงเวลาเป็นจำนวน time steps โดยปัดเศษและกำหนดให้มีอย่างน้อย 1 step
        total_steps += seg_steps # เก็บสะสมจำนวน steps ทั้งหมดไว้ใน total_steps

        boundaries.append(total_steps) 

    return boundaries
    # คืนค่า list boundaries ที่เก็บค่าสะสมของ time steps ณ จุดสิ้นสุดของแต่ละ segment
    # ตัวอย่างเช่น [0, 5, 12, 18] หมายถึง segment แรกใช้ 5 steps, segment ที่สองใช้ 7 steps, และ segment ที่สามใช้ 6 steps
# -----------------------------------------------------------------------------

    


def compute_agent_timeline(path, t_per_meter, simulation_time_step, max_time_steps):
    """
    คำนวณ timeline ของ agent ตาม path ที่ให้
      - ใช้ geodesic distance ในการคำนวณเวลาเดินแต่ละ segment
      - simulation_time_step คือความยาวของ time step (วินาที)
      - max_time_steps คือจำนวน time step สูงสุดที่ agent จะเดิน (เมื่อครบแล้วจะหยุด)
    คืนค่า timeline เป็น list ของตำแหน่ง [lat, lon] สำหรับแต่ละ time step
    """
    timeline = []
    total_steps = 0
    for i in range(len(path)-1):
        start = path[i]
        end = path[i+1]
        d = geodesic(start, end).meters
        seg_time = d * t_per_meter  # เวลาเดินในหน่วยวินาที
        seg_steps = max(1, int(round(seg_time / simulation_time_step)))
        for step in range(seg_steps):
            # หากจำนวน time steps รวมเกิน max_time_steps ให้หยุดทันที
            if total_steps >= max_time_steps:
                return timeline[:max_time_steps]
            fraction = step / seg_steps
            timeline.append(interpolate_position(start, end, fraction))
            total_steps += 1
    # เติมตำแหน่งสุดท้าย (จุดหมายปลายทาง) ถ้ายังไม่ครบ max_time_steps
    while len(timeline) < max_time_steps:
        timeline.append(path[-1])
    return timeline[:max_time_steps]



# -----------------------------------------------------------------------------
# ส่วน CBS: นิยาม class และฟังก์ชันสำหรับ Conflict-Based Search


# -----------------------------------------------------------------------------
# 3️⃣ ฟังก์ชัน create_map(...) → สร้างแผนที่และฝัง JavaScript animation
def create_map(full_paths, agents_positions, station_locations, station_bikes_timeline, destination_positions):
    m = folium.Map(location=[13.728, 100.775], zoom_start=15)
    for path in full_paths:
        folium.PolyLine(path, color='yellow', weight=2).add_to(m)
    for i, dest in enumerate(destination_positions):
        folium.Marker(
            location=[dest[0], dest[1]],
            popup=f"Destination {i + 1}",
            icon=folium.Icon(color="gray", icon="flag"),
        ).add_to(m)
    agents_positions_json = json.dumps(agents_positions)
    station_locations_json = json.dumps(station_locations)
    station_bikes_timeline_json = json.dumps(station_bikes_timeline)
    map_var = m.get_name()
    custom_js = f"""
    <script>
    window.addEventListener('load', function() {{
        var agentsPositions = {agents_positions_json};
        var stationLocations = {station_locations_json};
        var stationBikesTimeline = {station_bikes_timeline_json};
        var mapObj = window["{map_var}"];
        var redIcon = L.icon({{
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.4/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        }});
        var greenIcon = L.icon({{
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.4/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        }});
        var agentMarkers = [];
        for (var i = 0; i < agentsPositions.length; i++) {{
            var marker = L.marker(agentsPositions[i][0], {{icon: redIcon}}).addTo(mapObj);
            marker.bindPopup("Agent " + (i+1));
            agentMarkers.push(marker);
        }}
        var stationMarkers = [];
        for (var i = 0; i < stationLocations.length; i++) {{
            var marker = L.marker(stationLocations[i], {{icon: greenIcon}}).addTo(mapObj);
            marker.bindPopup("Station: " + stationLocations[i] + "<br>Bikes Available: " + stationBikesTimeline[0][i]);
            stationMarkers.push(marker);
        }}
        var timeStep = 0;
        var maxStep = agentsPositions[0].length;
        var interval = null;
        function updateMarkers() {{
            for (var i = 0; i < agentMarkers.length; i++) {{
                agentMarkers[i].setLatLng(agentsPositions[i][timeStep]);
            }}
            for (var i = 0; i < stationMarkers.length; i++) {{
                stationMarkers[i].setPopupContent("Station: " + stationLocations[i] + "<br>Bikes Available: " + stationBikesTimeline[timeStep][i]);
            }}
            document.getElementById("timeStepDisplay").innerText = "Time Step: " + timeStep;
        }}
        function startAnimation() {{
            if (!interval) {{
                interval = setInterval(function() {{
                    if (timeStep < maxStep - 1) {{
                        timeStep++;
                        updateMarkers();
                    }} else {{
                        clearInterval(interval);
                        interval = null;
                    }}
                }}, 100);
            }}
        }}
        function pauseAnimation() {{
            clearInterval(interval);
            interval = null;
        }}
        function resetAnimation() {{
            pauseAnimation();
            timeStep = 0;
            updateMarkers();
        }}
        document.getElementById("startBtn").addEventListener("click", startAnimation);
        document.getElementById("pauseBtn").addEventListener("click", pauseAnimation);
        document.getElementById("resetBtn").addEventListener("click", resetAnimation);
        updateMarkers();
    }});
    </script>
    """
    control_html = """
    <div style="text-align:center; margin-top: 10px;">
        <button id="startBtn">Start</button>
        <button id="pauseBtn">Pause</button>
        <button id="resetBtn">Reset</button>
        <p id="timeStepDisplay">Time Step: 0</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(control_html + custom_js))
    return m

# -----------------------------------------------------------------------------
# 4️⃣ ฟังก์ชัน run_simulation() → รันการจำลองและเปรียบเทียบ ABS กับ CBS
def run_simulation():
    num_persons = st.session_state.num_persons
    max_time_step = st.session_state.max_time_step
    num_bikes_per_station = st.session_state.num_bikes

    # ตั้งค่าความเร็วเดินและ simulation time step
    t_per_meter = 0.1           # เวลาที่ใช้เดิน 1 เมตร (วินาที)
    simulation_time_step = 1    # 1 วินาทีต่อ time step

    # กำหนดสถานีจักรยาน
    station_locations = [
        (13.7279, 100.7707),
        (13.7277, 100.7644),
        (13.7295, 100.7750),
        (13.7296, 100.7800),
        (13.7307, 100.7809),
        (13.7265, 100.7752),
        (13.7292, 100.7774)
    ]
    min_lat = min(x[0] for x in station_locations)
    max_lat = max(x[0] for x in station_locations)
    min_lon = min(x[1] for x in station_locations)
    max_lon = max(x[1] for x in station_locations)

    # สุ่มตำแหน่งเริ่มต้นและปลายทางของ agent สำหรับ ABS/CBS
    start_positions = [
        (random.uniform(min_lat, max_lat), random.uniform(min_lon, max_lon))
        for _ in range(num_persons)
    ]
    destination_positions = [
        (random.uniform(min_lat, max_lat), random.uniform(min_lon, max_lon))
        for _ in range(num_persons)
    ]

    # สร้างกราฟสำหรับ A* Search ระหว่างสถานี (ใช้เป็นพื้นที่ค้นหา)
    graph = {}
    for i, station in enumerate(station_locations):
        graph[station] = {}
        for j, neighbor in enumerate(station_locations):
            if i != j:
                graph[station][neighbor] = heuristic(station, neighbor)

    # กำหนดจำนวนจักรยานเริ่มต้นในแต่ละสถานี
    initial_station_bikes = [num_bikes_per_station] * len(station_locations)

    # ----------------------------------------------------------------------------------------------------------------
    #! ส่วน A* Alogorithm
    full_paths_abs = [] 
    rental_events = []  
    return_events = []  
    agent_grid_steps = []  # จำนวน grid steps ที่แต่ละ agent เดิน (ก่อน padding)

    for start_pos, dest_pos in zip(start_positions, destination_positions):
        print(f"ABS: Agent เริ่มที่ {start_pos} และต้องไปที่ {dest_pos}")

        # จัดเรียงสถานีทั้งหมดตามระยะทางจาก agent (ใกล้ -> ไกล) เพราะจะเช็คสถานีที่ใกล้ที่สุดก่อน , ถ้าสถานีนั้น ไม่มีจักรยาน → ให้เลือก สถานีที่ใกล้รองลงมา แต่ถ้ายังไม่มี → เลือกสถานีรองที่เหลือไปเรื่อย ๆ
        sorted_stations = sorted(station_locations, key=lambda s: heuristic(start_pos, s))

        # ค้นหาสถานีที่มีจักรยานเหลืออยู่
        start_station = None
        for station in sorted_stations:
            station_index = station_locations.index(station) # หา index ของสถานีนี้
            if initial_station_bikes[station_index] > 0: # ตรวจสอบว่ามีจักรยานหรือไม่
                start_station = station
                break
        if start_station is None:
            start_station = sorted_stations[0]

        # สำหรับ drop-off (สถานีปลายทาง) เราเลือก 𝘀𝘁𝗮𝘁𝗶𝗼𝗻 ที่ใกล้ 𝗱𝗲𝘀𝘁𝗶𝗻𝗮𝘁𝗶𝗼𝗻 มากที่สุด
        end_station = min(station_locations, key=lambda s: heuristic(dest_pos, s))

        # ขั้นตอน สร้างเส้นทาง: จุดเริ่มต้น → สถานีเช่า → (เส้นทาง A* ระหว่างสถานี) → จุดหมายปลายทาง
        # 1. จุดเริ่มต้น → สถานีเช่า
        # complete_path : list ที่เก็บเส้นทางของ agent ตั้งแต่เริ่มต้น จุดแรกคือ ตำแหน่งเริ่มต้นของ agent, จุดที่สองคือ สถานีเช่าจักรยาน (start_station) ที่เลือกไว้
        complete_path = [start_pos]

        # 2. สถานีเช่า → สถานีคืน (ด้วย a* alogorithm ⛩️)
        #! 🚩 เอาแบบนี้ไปก่อน เราต้องใช้ a* algotithm หาแค่สถานียืมไปสถานีคืน
        complete_path.extend(a_star_search(graph, start_station, end_station))

        # 3. สถานีคืน → จุดหมายปลายทาง
        complete_path.append(dest_pos)

        # full_paths เป็น list ที่เก็บเส้นทางของ agent ทุกคน
        full_paths_abs.append(complete_path)


        # คำนวณเวลาที่ใช้เดินในแต่ละ segment
        # คำนวณ segment boundaries ของ complete_path (ในหน่วย time step)
        boundaries = compute_segment_boundaries(complete_path, t_per_meter, simulation_time_step)

        # จำนวน grid steps ที่ agent เดินจริง (ก่อนถึงจุดสิ้นสุดของ path)
        active_steps = boundaries[-1]

        # หาก active_steps เกิน max_time_step ให้ถือว่าเดิน max_time_step
        if active_steps > max_time_step:
            active_steps = max_time_step
        agent_grid_steps.append(active_steps)

        # rental event: เมื่อ agent ถึงสถานีเช่า (complete_path[1])
        rental_time = boundaries[1] if boundaries[1] < max_time_step else max_time_step - 1

        # return event: เมื่อ agent ถึงสถานีคืน (complete_path[-2])
        return_time = boundaries[-2] if boundaries[-2] < max_time_step else max_time_step - 1

        # บันทึก event
        station_index = station_locations.index(start_station)
        end_station_index = station_locations.index(end_station)
        rental_events.append((rental_time, station_index))
        return_events.append((return_time, end_station_index))

        # ปรับจำนวนจักรยานในสถานีทันที
        initial_station_bikes[station_index] -= 1
        initial_station_bikes[end_station_index] += 1

    st.write("### ABS: จำนวน Grid Steps ที่แต่ละ Agent เดิน")
    for idx, steps in enumerate(agent_grid_steps):
        st.write(f"Agent {idx+1}: {steps} grid steps")

    # คำนวณตำแหน่งของ agent ในแต่ละ time step โดยใช้ compute_agent_timeline
    agents_positions_abs = []
    for path in full_paths_abs:
        timeline = compute_agent_timeline(path, t_per_meter, simulation_time_step, max_time_step)
        agents_positions_abs.append(timeline)

    
    

    # กำหนด CSS
    map_style = """
    <style>
        .stVerticalBlock { width: 100% !important; }
        .st-emotion-cache-17vd2cm { width: 100% !important; }
        [data-testid="stAppViewContainer"] { }
        [data-testid="stIFrame"] { width: 100% !important; height: 650px !important; }
        [data-testid="stMainBlockContainer"] { width: 100% !important; max-width: 100% !important; }
    </style>
    """
    st.markdown(map_style, unsafe_allow_html=True)
    

    # ส่งข้อมูล A* ไปสร้าง map
    st.write("### ABS Traffic Simulation Map")
    traffic_map_abs = create_map(full_paths_abs, agents_positions_abs, station_locations, 
                                 [[num_bikes_per_station]*len(station_locations) for _ in range(max_time_step)],
                                 destination_positions)
    with st.container():
        components.html(traffic_map_abs._repr_html_(), height=600)
    

  






    



# -----------------------------------------------------------------------------
# 5️⃣ ส่วนอินพุต Streamlit
st.title("Traffic Simulation: ABS vs CBS (Conflict-Based Search)")
st.number_input("Number of Agents:", min_value=1, value=5, key='num_persons')
st.number_input("Max Time Steps:", min_value=1, value=100, key='max_time_step')
st.number_input("Number of Bikes per Station:", min_value=1, value=10, key='num_bikes')

if st.button("Run Simulation"):
    run_simulation()


